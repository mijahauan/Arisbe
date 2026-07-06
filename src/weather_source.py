"""The first **live resolving-membrane source** — NWS weather, forecast-vs-actual.

Design-of-record: ``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b (the raise-and-resolve
membrane, ``resolving_membrane.py``) + §18 (run 7). Affirmed ordering (2026-07-05): the
first live *resolving* source lands before the docket's Q2/Q3 tiers, because wiki-only
starves the game's inductive/refutational registers — this source supplies the missing
event class **hourly**: a standing forecast met by an observation.

**The theory under test is seeded, not discovered.** M carries the naive laws
*"what is forecast, happens"*::

    ~[ (forecast_temp_band *s *t *b) ~[ (temp_band s t b) ] ]
    ~[ (forecast_precip *s *t) ~[ (precip s t) ] ]

Forecast *arrivals* enter M as plain facts (``forecast_temp_band`` /
``forecast_precip`` atoms); materialization forward-chains them into predictions; and
when the hour has passed, the observation resolves each claim through the ordinary
:class:`resolving_membrane.ResolvingItem` mechanics — a **hit** scores the ledger, a
**miss** arrives in the law-refuting shape ``(forecast…) ~[ (actual…) ]`` that the
mechanical Challenger relinquishes a standing law over. The run's story is empirical:
how long does the naive theory survive, and with what net score, per claim kind.

**Two-phase fetch (the two-clock structure a resolving source needs).** Each poll:

1. *Raise* — fetch the hourly forecast per station; hours within the horizon not yet
   claimed become **pending claims** and emit their forecast-arrival atoms.
2. *Resolve* — fetch recent observations; every pending claim whose hour has fully
   passed is scored against the observation falling inside that hour and emitted as a
   resolution item. A matured claim with **no** observation in its window is dropped
   *counted* after a grace period (``unresolved_dropped`` — never silent).

Offline/CI-safe by construction: the network call is injectable (``fetch_json=``), and
every emitted batch is recorded to ``record_path`` (JSONL) so a live run replays
offline (``replay_item_batches`` → ``live_runner.ReplaySource`` — the determinism
canary). ``save_state``/``load_state`` persist pending claims across a crash/resume.
Correspondence-not-truth: NWS data is low-warrant input; M earns a track record, never
truth. Additive; no protected module touched.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from resolving_membrane import ResolvingItem

NWS_API = "https://api.weather.gov"
USER_AGENT = "Arisbe-EPG/0.1 (research; michael.j.hauan@gmail.com)"

# A small default constellation: climatically diverse, reliable METAR stations.
DEFAULT_STATIONS: Dict[str, Tuple[float, float]] = {
    "KAUS": (30.183, -97.680),    # Austin
    "KSEA": (47.444, -122.314),   # Seattle
    "KBOS": (42.361, -71.010),    # Boston
    "KDEN": (39.847, -104.656),   # Denver
    "KMIA": (25.788, -80.317),    # Miami
}

LAW_TEMP = "~[ (forecast_temp_band *s *t *b) ~[ (temp_band s t b) ] ]"
LAW_PRECIP = "~[ (forecast_precip *s *t) ~[ (precip s t) ] ]"
SEED_LAWS = [LAW_TEMP, LAW_PRECIP]

_PRECIP_RE = re.compile(r"rain|snow|drizzle|shower|thunder|sleet|hail", re.I)


def _live_fetch_json(url: str) -> dict:
    """The real HTTP call — stdlib urllib + certifi TLS + the etiquette User-Agent
    NWS requires. Never invoked in CI (tests inject ``fetch_json``)."""
    import ssl
    import urllib.request
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def band_of(temp_f: float, width: int = 5) -> str:
    """The claim's discretization: a temperature band label, e.g. 76.3°F → "75-79"
    at width 5. Bands make the forecast a checkable proposition rather than a point
    estimate no observation would ever exactly match."""
    lo = int(temp_f // width) * width
    return f"{lo}-{lo + width - 1}"


def _hour_utc(iso: str) -> str:
    """Normalize an ISO timestamp (any offset) to its UTC hour label — the claim's
    time constant, e.g. "2026-07-07T02Z"."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%HZ")


def _hour_dt(hour_label: str) -> datetime:
    return datetime.strptime(hour_label, "%Y-%m-%dT%HZ").replace(tzinfo=timezone.utc)


@dataclass
class PendingClaim:
    """A raised, not-yet-resolved forecast claim."""
    station: str
    hour: str            # UTC hour label
    kind: str            # "temp" | "precip"
    value: Optional[str]  # the forecast band (temp) or None (precip)

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.station, self.hour, self.kind)


class WeatherSource:
    """A :class:`live_runner.LiveSource` of :class:`ResolvingItem`s (see module
    docstring). ``horizon_hours`` bounds how far ahead claims are raised;
    ``grace_hours`` how long a matured claim waits for an observation before being
    dropped counted; ``pop_threshold`` the probability-of-precipitation (%) at or
    above which a precip claim is raised."""

    def __init__(
        self,
        stations: Optional[Dict[str, Tuple[float, float]]] = None,
        *,
        horizon_hours: int = 6,
        grace_hours: int = 3,
        band_width: int = 5,
        pop_threshold: int = 60,
        fetch_json: Optional[Callable[[str], dict]] = None,
        record_path: Optional[str] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ):
        self._stations = dict(stations or DEFAULT_STATIONS)
        self._horizon = horizon_hours
        self._grace = grace_hours
        self._width = band_width
        self._pop = pop_threshold
        self._fetch = fetch_json or _live_fetch_json
        self._record = record_path
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._forecast_urls: Dict[str, str] = {}
        self._pending: Dict[Tuple[str, str, str], PendingClaim] = {}
        self._claimed: set = set()          # keys ever raised (never re-claim an hour)
        # Counters — never silent.
        self.claims_raised = 0
        self.resolutions = 0
        self.unresolved_dropped = 0
        self.fetch_errors = 0

    # -- NWS plumbing -----------------------------------------------------------

    def _forecast_url(self, station: str) -> Optional[str]:
        if station not in self._forecast_urls:
            lat, lon = self._stations[station]
            try:
                meta = self._fetch(f"{NWS_API}/points/{lat},{lon}")
                self._forecast_urls[station] = meta["properties"]["forecastHourly"]
            except Exception:
                self.fetch_errors += 1
                return None
        return self._forecast_urls[station]

    def _hourly_forecast(self, station: str) -> List[dict]:
        url = self._forecast_url(station)
        if not url:
            return []
        try:
            data = self._fetch(url)
            return data["properties"]["periods"]
        except Exception:
            self.fetch_errors += 1
            return []

    def _recent_observations(self, station: str) -> List[dict]:
        try:
            data = self._fetch(f"{NWS_API}/stations/{station}/observations?limit=12")
            return [f["properties"] for f in data.get("features", [])]
        except Exception:
            self.fetch_errors += 1
            return []

    # -- phase 1: raise ----------------------------------------------------------

    def _raise_claims(self, now: datetime) -> List[ResolvingItem]:
        items: List[ResolvingItem] = []
        limit = now + timedelta(hours=self._horizon)
        for st in self._stations:
            for period in self._hourly_forecast(st):
                try:
                    start = datetime.fromisoformat(
                        period["startTime"].replace("Z", "+00:00"))
                except Exception:
                    continue
                if not (now <= start <= limit):
                    continue
                hour = _hour_utc(period["startTime"])
                temp = period.get("temperature")
                if isinstance(temp, (int, float)):
                    key = (st, hour, "temp")
                    if key not in self._claimed:
                        b = band_of(float(temp), self._width)
                        self._claimed.add(key)
                        self._pending[key] = PendingClaim(st, hour, "temp", b)
                        self.claims_raised += 1
                        items.append(ResolvingItem(
                            f'(forecast_temp_band "{st}" "{hour}" "{b}")',
                            happened=True))
                pop = ((period.get("probabilityOfPrecipitation") or {}).get("value"))
                if isinstance(pop, (int, float)) and pop >= self._pop:
                    key = (st, hour, "precip")
                    if key not in self._claimed:
                        self._claimed.add(key)
                        self._pending[key] = PendingClaim(st, hour, "precip", None)
                        self.claims_raised += 1
                        items.append(ResolvingItem(
                            f'(forecast_precip "{st}" "{hour}")', happened=True))
        return items

    # -- phase 2: resolve ---------------------------------------------------------

    @staticmethod
    def _obs_in_hour(observations: List[dict], hour: str) -> Optional[dict]:
        start = _hour_dt(hour)
        end = start + timedelta(hours=1)
        best = None
        for obs in observations:
            try:
                ts = datetime.fromisoformat(obs["timestamp"].replace("Z", "+00:00"))
            except Exception:
                continue
            if start <= ts < end and (best is None or ts > best[0]):
                best = (ts, obs)
        return best[1] if best else None

    @staticmethod
    def _obs_precip(obs: dict) -> bool:
        wx = " ".join(str(w.get("weather") or w.get("rawString") or "")
                      for w in (obs.get("presentWeather") or []))
        if _PRECIP_RE.search(wx) or _PRECIP_RE.search(str(obs.get("textDescription", ""))):
            return True
        last = (obs.get("precipitationLastHour") or {}).get("value")
        return isinstance(last, (int, float)) and last > 0

    def _resolve_matured(self, now: datetime) -> List[ResolvingItem]:
        items: List[ResolvingItem] = []
        by_station: Dict[str, List[dict]] = {}
        for key in sorted(self._pending):
            claim = self._pending[key]
            hour_end = _hour_dt(claim.hour) + timedelta(hours=1)
            if now < hour_end:
                continue                                    # not yet matured
            if claim.station not in by_station:
                by_station[claim.station] = self._recent_observations(claim.station)
            obs = self._obs_in_hour(by_station[claim.station], claim.hour)
            if obs is None:
                if now > hour_end + timedelta(hours=self._grace):
                    del self._pending[key]                  # counted, never silent
                    self.unresolved_dropped += 1
                continue
            del self._pending[key]
            self.resolutions += 1
            st, hour = claim.station, claim.hour
            if claim.kind == "temp":
                temp_c = (obs.get("temperature") or {}).get("value")
                if not isinstance(temp_c, (int, float)):
                    self.unresolved_dropped += 1
                    continue
                obs_band = band_of(temp_c * 9 / 5 + 32, self._width)
                claim_egif = f'(temp_band "{st}" "{hour}" "{claim.value}")'
                if obs_band == claim.value:
                    items.append(ResolvingItem(claim_egif, happened=True))
                else:
                    items.append(ResolvingItem(
                        claim_egif, happened=False,
                        world_egif=(f'(forecast_temp_band "{st}" "{hour}" "{claim.value}") '
                                    f'~[ (temp_band "{st}" "{hour}" "{claim.value}") ] '
                                    f'(temp_band "{st}" "{hour}" "{obs_band}")')))
            else:                                           # precip
                happened = self._obs_precip(obs)
                claim_egif = f'(precip "{st}" "{hour}")'
                if happened:
                    items.append(ResolvingItem(claim_egif, happened=True))
                else:
                    items.append(ResolvingItem(
                        claim_egif, happened=False,
                        world_egif=(f'(forecast_precip "{st}" "{hour}") '
                                    f'~[ (precip "{st}" "{hour}") ]')))
        return items

    # -- the LiveSource shape ------------------------------------------------------

    def fetch(self) -> Sequence[ResolvingItem]:
        now = self._clock()
        items = self._raise_claims(now) + self._resolve_matured(now)
        if self._record and items:
            with open(self._record, "a", encoding="utf-8") as fh:
                fh.write(json.dumps([asdict(i) for i in items]) + "\n")
        return items

    def exhausted(self) -> bool:
        return False                                        # the weather does not end

    # -- crash/resume ---------------------------------------------------------------

    def save_state(self, path: str) -> None:
        state = {
            "forecast_urls": self._forecast_urls,
            "pending": [asdict(c) for c in self._pending.values()],
            "claimed": sorted(list(k) for k in self._claimed),
            "counters": {"claims_raised": self.claims_raised,
                         "resolutions": self.resolutions,
                         "unresolved_dropped": self.unresolved_dropped,
                         "fetch_errors": self.fetch_errors},
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)

    @classmethod
    def load_state(cls, path: str, **kwargs) -> "WeatherSource":
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        src = cls(**kwargs)
        src._forecast_urls = dict(state.get("forecast_urls", {}))
        for d in state.get("pending", []):
            c = PendingClaim(**d)
            src._pending[c.key] = c
        src._claimed = {tuple(k) for k in state.get("claimed", [])}
        c = state.get("counters", {})
        src.claims_raised = c.get("claims_raised", 0)
        src.resolutions = c.get("resolutions", 0)
        src.unresolved_dropped = c.get("unresolved_dropped", 0)
        src.fetch_errors = c.get("fetch_errors", 0)
        return src


def replay_item_batches(path: str) -> List[List[ResolvingItem]]:
    """Read a ``record_path`` file back into per-poll batches of
    :class:`ResolvingItem` — hand to ``live_runner.ReplaySource`` to re-drive the
    identical trajectory offline (the determinism canary)."""
    batches: List[List[ResolvingItem]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                batches.append([ResolvingItem(**d) for d in json.loads(line)])
    return batches


__all__ = ["WeatherSource", "PendingClaim", "ResolvingItem", "band_of",
           "replay_item_batches", "DEFAULT_STATIONS", "SEED_LAWS",
           "LAW_TEMP", "LAW_PRECIP"]
