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
import time
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

# A wet Gulf / Southeast constellation — summer daily convection gives high PoP,
# so the *precipitation* arm actually raises and resolves claims (RUN_9_LOG F2⁹:
# the precip arm was inert because PoP never reached the gate). Not in the default
# set; named by ICAO on the command line.
WET_STATIONS: Dict[str, Tuple[float, float]] = {
    "KMIA": (25.788, -80.317),    # Miami
    "KTPA": (27.976, -82.533),    # Tampa
    "KMSY": (29.993, -90.258),    # New Orleans
    "KIAH": (29.980, -95.360),    # Houston (Intercontinental)
    "KJAX": (30.494, -81.688),    # Jacksonville
    "KMCO": (28.429, -81.309),    # Orlando
    "KFLL": (26.072, -80.153),    # Fort Lauderdale
}

# The full table the driver can resolve an ICAO against (defaults + wet).
KNOWN_STATIONS: Dict[str, Tuple[float, float]] = {**DEFAULT_STATIONS, **WET_STATIONS}

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


def band_bounds(temp_f: float, width: int = 5, *,
                center: Optional[float] = None) -> Tuple[int, str]:
    """Return ``(lo, label)`` for a temperature band — the claim's discretization.

    Two modes (run 9, F2⁸):

    - **grid** (``center=None``) — bins are aligned to a fixed ``[k·width, …)``
      grid, so ``76.3°F → (75, "75-79")`` at width 5. A forecast near a grid edge
      is *fragile*: a small observation error can cross the boundary and miss even
      a well-calibrated band — the mechanism RUN_8_LOG F2⁸ implicates in the
      positive-net limit cycle.
    - **centered** (``center`` = the forecast) — the band is centered on the
      forecast value, so ``79°F → (77, "77-81")``: a miss happens only when the
      observation is more than ``width/2`` off the forecast, symmetric and
      edge-fragility-free. Run 9 tests whether this converts the limit cycle to a
      fixed point, or whether a noisy domain always limit-cycles.

    The interval is half-open ``[lo, lo+width)`` (matching the grid), so a
    fractional observation lands in exactly one band."""
    if center is None:
        lo = int(temp_f // width) * width
    else:
        lo = int(round(center)) - width // 2
    return lo, f"{lo}-{lo + width - 1}"


def band_of(temp_f: float, width: int = 5) -> str:
    """The grid band label — the run-7/8 discretization (and a plain descriptor of
    an observed value). See :func:`band_bounds` for centered bins (run 9)."""
    return band_bounds(temp_f, width)[1]


def _hour_utc(iso: str) -> str:
    """Normalize an ISO timestamp (any offset) to its UTC hour label — the claim's
    time constant, e.g. "2026-07-07T02Z"."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%HZ")


def _hour_dt(hour_label: str) -> datetime:
    return datetime.strptime(hour_label, "%Y-%m-%dT%HZ").replace(tzinfo=timezone.utc)


@dataclass
class PendingClaim:
    """A raised, not-yet-resolved forecast claim.

    ``width`` records the temperature band width the claim was raised under, so a
    mid-run re-generalization (a wider band) only affects *newly* raised claims —
    an in-flight claim resolves against the discretization it was made with, not
    the current one (else every pending claim would spuriously miss on a widen).
    ``None`` for precip claims and for state written before the field existed.
    """
    station: str
    hour: str            # UTC hour label
    kind: str            # "temp" | "precip"
    value: Optional[str]  # the forecast band (temp) or None (precip)
    width: Optional[int] = None  # band width at raise time (temp only)
    band_lo: Optional[int] = None  # band lower bound at raise time (temp only) —
    # carries the exact interval [band_lo, band_lo+width) so resolution is one
    # half-open containment check, mode-independent (grid or centered). ``None``
    # for precip and for state written before centered bins (F2⁸) existed.

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
        bin_mode: str = "grid",
        fetch_json: Optional[Callable[[str], dict]] = None,
        record_path: Optional[str] = None,
        clock: Optional[Callable[[], datetime]] = None,
        sleep: Optional[Callable[[float], None]] = None,
        fetch_tries: int = 3,
        fetch_backoff: float = 0.5,
    ):
        self._stations = dict(stations or DEFAULT_STATIONS)
        self._horizon = horizon_hours
        self._grace = grace_hours
        self._width = band_width
        self._pop = pop_threshold
        if bin_mode not in ("grid", "centered"):
            raise ValueError(f"bin_mode must be 'grid' or 'centered', got {bin_mode!r}")
        self._bin_mode = bin_mode
        self._fetch = fetch_json or _live_fetch_json
        self._record = record_path
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # F1⁷: a bounded retry with backoff around the flaky NWS endpoints; the
        # sleep is injectable (default time.sleep, a no-op capture in tests) so CI
        # stays fast and deterministic — mirrors ``clock``.
        self._sleep = sleep or time.sleep
        self._fetch_tries = max(1, fetch_tries)
        self._fetch_backoff = fetch_backoff
        self._forecast_urls: Dict[str, str] = {}
        self._pending: Dict[Tuple[str, str, str], PendingClaim] = {}
        self._claimed: set = set()          # keys ever raised (never re-claim an hour)
        # Counters — never silent.
        self.claims_raised = 0
        self.resolutions = 0
        self.unresolved_dropped = 0
        # F3⁸ (run 9): per-arm claim/resolution counts, so a *dormant arm* is
        # visible — a precip arm that never matured (few resolutions) is
        # distinguishable from one that was simply well-calibrated (many
        # resolutions, all hits). Keyed "temp" | "precip".
        self.claims_raised_by_kind: Dict[str, int] = {}
        self.resolutions_by_kind: Dict[str, int] = {}
        self.fetch_errors = 0               # aggregate (back-compat)
        # F1⁷: per-station error counts so a *dark station* is visible in the
        # digest, not just folded into the aggregate.
        self.fetch_errors_by_station: Dict[str, int] = {}

    # -- NWS plumbing -----------------------------------------------------------

    def _fetch_retry(self, url: str) -> dict:
        """``self._fetch(url)`` with a bounded exponential backoff (F1⁷).

        Retries a failed fetch ``self._fetch_tries`` times, sleeping
        ``backoff · 2^attempt`` between tries via the injectable ``self._sleep``.
        Re-raises the last exception when every attempt fails — the caller counts
        it once (per station) and degrades gracefully.  No counting here, so a
        successful retry is invisible except in the reduced error rate.
        """
        last: Exception = RuntimeError("no fetch attempted")
        for attempt in range(self._fetch_tries):
            try:
                return self._fetch(url)
            except Exception as exc:              # transient 5xx/timeout — retry
                last = exc
                if attempt + 1 < self._fetch_tries:
                    self._sleep(self._fetch_backoff * (2.0 ** attempt))
        raise last

    def _note_fetch_error(self, station: str) -> None:
        """Count a fetch failure — aggregate + per-station (F1⁷)."""
        self.fetch_errors += 1
        self.fetch_errors_by_station[station] = (
            self.fetch_errors_by_station.get(station, 0) + 1)

    def _count_raise(self, kind: str) -> None:
        """Count a raised claim — aggregate + per-arm (F3⁸)."""
        self.claims_raised += 1
        self.claims_raised_by_kind[kind] = (
            self.claims_raised_by_kind.get(kind, 0) + 1)

    def _count_resolve(self, kind: str) -> None:
        """Count a resolved (matured + scored) claim — aggregate + per-arm (F3⁸)."""
        self.resolutions += 1
        self.resolutions_by_kind[kind] = (
            self.resolutions_by_kind.get(kind, 0) + 1)

    def _forecast_url(self, station: str) -> Optional[str]:
        if station not in self._forecast_urls:
            lat, lon = self._stations[station]
            try:
                meta = self._fetch_retry(f"{NWS_API}/points/{lat},{lon}")
                self._forecast_urls[station] = meta["properties"]["forecastHourly"]
            except Exception:
                self._note_fetch_error(station)
                return None
        return self._forecast_urls[station]

    def _hourly_forecast(self, station: str) -> List[dict]:
        url = self._forecast_url(station)
        if not url:
            return []
        try:
            data = self._fetch_retry(url)
            return data["properties"]["periods"]
        except Exception:
            self._note_fetch_error(station)
            return []

    def _recent_observations(self, station: str) -> List[dict]:
        try:
            data = self._fetch_retry(
                f"{NWS_API}/stations/{station}/observations?limit=12")
            return [f["properties"] for f in data.get("features", [])]
        except Exception:
            self._note_fetch_error(station)
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
                        # Centered bins (F2⁸) center the band on the forecast;
                        # grid bins snap it to a fixed grid — see band_bounds.
                        center = float(temp) if self._bin_mode == "centered" else None
                        lo, b = band_bounds(float(temp), self._width, center=center)
                        self._claimed.add(key)
                        self._pending[key] = PendingClaim(
                            st, hour, "temp", b, width=self._width, band_lo=lo)
                        self._count_raise("temp")
                        items.append(ResolvingItem(
                            f'(forecast_temp_band "{st}" "{hour}" "{b}")',
                            happened=True))
                pop = ((period.get("probabilityOfPrecipitation") or {}).get("value"))
                if isinstance(pop, (int, float)) and pop >= self._pop:
                    key = (st, hour, "precip")
                    if key not in self._claimed:
                        self._claimed.add(key)
                        self._pending[key] = PendingClaim(st, hour, "precip", None)
                        self._count_raise("precip")
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
            st, hour = claim.station, claim.hour
            if claim.kind == "temp":
                temp_c = (obs.get("temperature") or {}).get("value")
                if not isinstance(temp_c, (int, float)):
                    # Matured with no usable observation → dropped, not a bet
                    # (never scored, so never counted as a resolution).
                    self.unresolved_dropped += 1
                    continue
                self._count_resolve("temp")
                obs_f = temp_c * 9 / 5 + 32
                w = claim.width or self._width
                # Resolve by half-open containment in the claim's own raise-time
                # band [band_lo, band_lo+w) — mode-independent (grid or centered),
                # and under the claim's own width, so a mid-run re-generalization
                # (a wider band) never spuriously misses a claim made under a
                # narrower band. band_lo is None only for pre-F2⁸ carried state;
                # fall back to a grid recompute there.
                if claim.band_lo is None:
                    hit = band_of(obs_f, w) == claim.value
                else:
                    hit = claim.band_lo <= obs_f < claim.band_lo + w
                obs_band = band_of(obs_f, w)  # a plain grid descriptor of the observed value
                claim_egif = f'(temp_band "{st}" "{hour}" "{claim.value}")'
                if hit:
                    items.append(ResolvingItem(claim_egif, happened=True))
                else:
                    items.append(ResolvingItem(
                        claim_egif, happened=False,
                        world_egif=(f'(forecast_temp_band "{st}" "{hour}" "{claim.value}") '
                                    f'~[ (temp_band "{st}" "{hour}" "{claim.value}") ] '
                                    f'(temp_band "{st}" "{hour}" "{obs_band}")')))
            else:                                           # precip
                self._count_resolve("precip")
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
            "claims_raised_by_kind": dict(self.claims_raised_by_kind),
            "resolutions_by_kind": dict(self.resolutions_by_kind),
            "fetch_errors_by_station": dict(self.fetch_errors_by_station),
            # The (possibly re-generalized) claim knobs, so a resume carries the
            # recalibrated discretization, not the seed defaults.
            "params": {"band_width": self._width, "pop_threshold": self._pop,
                       "bin_mode": self._bin_mode},
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
        src.claims_raised_by_kind = dict(state.get("claims_raised_by_kind", {}))
        src.resolutions_by_kind = dict(state.get("resolutions_by_kind", {}))
        src.fetch_errors_by_station = dict(state.get("fetch_errors_by_station", {}))
        p = state.get("params", {})
        src._width = p.get("band_width", src._width)
        src._pop = p.get("pop_threshold", src._pop)
        src._bin_mode = p.get("bin_mode", src._bin_mode)
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
           "band_bounds", "replay_item_batches", "DEFAULT_STATIONS",
           "WET_STATIONS", "KNOWN_STATIONS", "SEED_LAWS",
           "LAW_TEMP", "LAW_PRECIP"]
