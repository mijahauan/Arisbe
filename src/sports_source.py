"""The **discrete** resolving-membrane source — MLB game outcomes, pick-vs-final.

Design-of-record: ``runs/RUN_12_LOG.md`` (pre-registered 2026-07-12) +
``docs/AUTOMATED_ENDOPOREUTIC_GAME.md`` §4b/§11.4. The weather trilogy (runs 7–11)
evidenced the **knob-type law** twice — *a refuted theory re-generalizes into a better
one only if its recalibration knob calibrates, not merely selects* — but both
evidences lean on weather's donated width (temperature is continuous) and on a skilled
expert forecast (NWS) as input. Run 12 removes both: a game is **won or lost** (no
width anywhere) and the input is raw standings, not an expert model. The question: is
the knob-type law a law of the *game*, or a fact about *weather*?

**Four arms over the same games**, kept separable by per-arm vocabularies (the
temp/precip precedent — one M, one runner, arms distinguished by relation name):

- **Arm A — the knob-type null** (``pick_naive`` → ``win_naive``, :data:`LAW_NAIVE`):
  picks the home team; carries **no mechanism at all** — never recalibrated, never
  reseeded. The law predicts it is refuted by the first home loss and falls silent
  (the run-10 trap shape). Its recovery would falsify the knob-type law's necessity
  half.
- **Arm B — the manufactured calibration knob** (``pick_fav``/``pick_dog`` →
  ``win_fav``/``win_dog``, :data:`LAW_FAV`/:data:`LAW_DOG`; the headline): a
  two-direction bet around a **learned cutpoint on win-percentage differential** (the
  F1¹¹ mechanism transplanted — the favorite when the differential ≥ cut, the
  underdog below it). The cut is recalibrated from the ledger
  (``sports_recalibration``) and its fallen laws reseeded — expect recovery.
- **Arm C — rival theories, the selection register** (``pick_home`` → ``win_home``,
  ``pick_strong`` → ``win_strong``, and — with an Odds API key — ``pick_odds`` →
  ``win_odds``; :data:`LAW_HOME`/:data:`LAW_STRONG`/:data:`LAW_ODDS`): home-wins,
  higher-win-pct-wins, and odds-favorite-wins bet on the *same* games, ranked live
  by ``resolving_membrane.select_best``. The rivals are **held** — reseeded
  verbatim when fallen — because the C register's instrument is the *ledger* (the
  world's track-record selection), not law standing; arm A is the standing
  instrument. The odds rival (decision (a), taken 2026-07-13) reads **The Odds API**
  (`the-odds-api.com`, ``h2h`` moneylines, decimal): the pick is the **consensus
  favorite** — lower average decimal price across the returned bookmakers; a
  cross-book tie is skipped *counted* (``odds_skipped``), an event with no posted
  market yet is retried until ~2 h before first pitch, then given up counted. The
  key rides only in the request URL (``odds_key=`` / the driver's ``ODDS_API_KEY``
  env) — never in recorded items, state files, or logs.
- **Arm D (induction-from-blank)** — not built; optional-if-time per the
  pre-registration.

**Claim mechanics** (the resolving-membrane shape, mirroring ``weather_source``):

1. *Raise* — poll the MLB Stats API schedule (free, no auth) for games starting
   within the horizon; each unclaimed game emits one pick fact per arm, e.g.
   ``(pick_strong "776001" "Harbor City")``. Materializing an arm's law derives the
   corresponding ``(win_… g t)`` — M's forecast, taken by the peel **before** the
   outcome arrives.
2. *Resolve* — poll the schedule for pending games' dates; a **Final** scores each
   arm's claim (hit iff the picked team won; a miss arrives in the law-refuting
   shape ``(pick_… g t) ~[ (win_… g t) ] (won g winner)`` so the mechanical
   Challenger relinquishes the over-general law). Postponed / suspended / cancelled
   games are dropped **counted** (``postponed_dropped``), and a game that never
   finalizes is dropped counted after a grace period — never silent.

The favorite is the team with the higher win percentage from the standings (a tie
breaks to the **home** team, documented); the differential is carried in integer
**thousandths** of win pct (e.g. ``.556 − .481 → 75``) so the cut is the same kind of
integer knob as run 11's PoP cut.

Offline/CI-safe by construction: the network call is injectable (``fetch_json=``),
every emitted batch is recorded to ``record_path`` (JSONL) so a live run replays
offline (:func:`replay_item_batches` → ``live_runner.ReplaySource`` — the determinism
canary), and ``save_state``/``load_state`` persist pending claims + the learned cut
across a crash/resume. Correspondence-not-truth: MLB data is low-warrant input; M
earns a track record, never truth. Additive; no protected module touched.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from resolving_membrane import ResolvingItem

MLB_API = "https://statsapi.mlb.com/api/v1"
ODDS_API = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
USER_AGENT = "Arisbe-EPG/0.1 (research; michael.j.hauan@gmail.com)"

# The seeded theories (arm D seeds nothing and is not built).
LAW_NAIVE = "~[ (pick_naive *g *t) ~[ (win_naive g t) ] ]"
LAW_HOME = "~[ (pick_home *g *t) ~[ (win_home g t) ] ]"
LAW_STRONG = "~[ (pick_strong *g *t) ~[ (win_strong g t) ] ]"
LAW_FAV = "~[ (pick_fav *g *t) ~[ (win_fav g t) ] ]"
LAW_DOG = "~[ (pick_dog *g *t) ~[ (win_dog g t) ] ]"
LAW_ODDS = "~[ (pick_odds *g *t) ~[ (win_odds g t) ] ]"

SEED_LAWS = [LAW_NAIVE, LAW_HOME, LAW_STRONG, LAW_FAV, LAW_DOG]
SEED_LAWS_ODDS = SEED_LAWS + [LAW_ODDS]       # when the odds rival runs (keyed)
# Arm C's rivals are HELD (reseeded verbatim when fallen) — the selection register
# scores theories by ledger, so a rival must keep betting; arm A never is.
HELD_LAWS = [LAW_HOME, LAW_STRONG]
HELD_LAWS_ODDS = HELD_LAWS + [LAW_ODDS]

# Raise-phase pick kinds. "cal" (arm B) resolves to a "fav" or "dog" claim per
# game; "odds" needs an Odds API key (or injected fetch) and is off by default.
DEFAULT_ARMS = ("naive", "home", "strong", "cal")
ARM_KINDS = DEFAULT_ARMS + ("odds",)

_POSTPONED = ("postponed", "suspended", "cancelled", "canceled")


def _live_fetch_json(url: str) -> dict:
    """The real HTTP call — stdlib urllib + certifi TLS + an etiquette User-Agent.
    Never invoked in CI (tests inject ``fetch_json``)."""
    import ssl
    import urllib.request
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _const(value: str) -> str:
    """A team/game label → an EGIF constant token: quotes/backslashes stripped and
    control characters replaced by spaces (the ``wikidata_source._const`` rule), so
    the string stays well-formed and single-line."""
    cleaned = "".join(
        c if c.isprintable() else " "
        for c in str(value).replace('"', "").replace("\\", ""))
    return cleaned.strip() or "?"


def _iso_dt(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(
            timezone.utc)
    except Exception:
        return None


def pct_of(wins: int, losses: int) -> float:
    """Win percentage; an unplayed team reads 0.5 (no evidence either way)."""
    games = wins + losses
    return (wins / games) if games else 0.5


def favorite_of(home: str, away: str, pct_home: float, pct_away: float
                ) -> Tuple[str, str, int]:
    """``(favorite, underdog, diff)`` — the higher-win-pct team, a tie breaking to
    the **home** team; ``diff`` in integer thousandths of win pct."""
    diff = int(round(abs(pct_home - pct_away) * 1000))
    if pct_home >= pct_away:
        return home, away, diff
    return away, home, diff


@dataclass
class PendingGame:
    """A raised, not-yet-resolved pick. ``kind`` is the *claim* kind
    (``naive``/``home``/``strong``/``fav``/``dog`` — arm B's "cal" raise becomes a
    fav or dog claim); ``team`` the picked team; ``diff`` the win-pct differential
    (thousandths) and ``cut`` the cutpoint at raise time (cal picks only), carried
    for the digest — resolution needs only the picked team vs the winner."""
    game_pk: str
    date: str            # schedule date, YYYY-MM-DD
    kind: str
    team: str
    game_time: str       # ISO gameDate — the grace clock starts here
    diff: Optional[int] = None
    cut: Optional[int] = None

    @property
    def key(self) -> Tuple[str, str]:
        return (self.game_pk, self.kind)


class SportsSource:
    """A ``live_runner.LiveSource`` of :class:`ResolvingItem`s (see module
    docstring). ``horizon_hours`` bounds how far ahead picks are raised;
    ``grace_hours`` how long a started-but-never-final game waits before being
    dropped counted; ``cut`` the arm-B win-pct-differential cutpoint (thousandths)
    at/above which the favorite is picked, below which the underdog."""

    def __init__(
        self,
        *,
        arms: Optional[Sequence[str]] = None,
        horizon_hours: int = 18,
        grace_hours: int = 12,
        cut: int = 50,
        fetch_json: Optional[Callable[[str], dict]] = None,
        odds_key: Optional[str] = None,
        odds_fetch: Optional[Callable[[], list]] = None,
        record_path: Optional[str] = None,
        clock: Optional[Callable[[], datetime]] = None,
        sleep: Optional[Callable[[float], None]] = None,
        fetch_tries: int = 3,
        fetch_backoff: float = 0.5,
    ):
        has_odds = odds_key is not None or odds_fetch is not None
        if arms is None:
            arms = ARM_KINDS if has_odds else DEFAULT_ARMS
        unknown = set(arms) - set(ARM_KINDS)
        if unknown:
            raise ValueError(f"unknown arms {sorted(unknown)!r} — pick from {ARM_KINDS}")
        if "odds" in arms and not has_odds:
            raise ValueError("the odds arm needs odds_key= (The Odds API) or an "
                             "injected odds_fetch=")
        self._arms = tuple(a for a in ARM_KINDS if a in set(arms))
        self._odds_fetch = odds_fetch or (
            (lambda: _live_fetch_json(
                f"{ODDS_API}?apiKey={odds_key}&regions=us&markets=h2h"
                f"&oddsFormat=decimal")) if odds_key else None)
        self._horizon = horizon_hours
        self._grace = grace_hours
        self._cut = cut
        self._fetch = fetch_json or _live_fetch_json
        self._record = record_path
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._sleep = sleep or time.sleep
        self._fetch_tries = max(1, fetch_tries)
        self._fetch_backoff = fetch_backoff
        self._pending: Dict[Tuple[str, str], PendingGame] = {}
        self._claimed: set = set()          # (game_pk, kind) ever raised
        # Counters — never silent.
        self.claims_raised = 0
        self.resolutions = 0
        self.unresolved_dropped = 0
        self.postponed_dropped = 0          # the pre-registered grace counter (P5¹²)
        self.odds_skipped = 0               # odds pick given up (tie / never posted)
        self.claims_raised_by_kind: Dict[str, int] = {}
        self.resolutions_by_kind: Dict[str, int] = {}
        self.fetch_errors = 0
        self.fetch_errors_by_endpoint: Dict[str, int] = {}

    # -- MLB plumbing ---------------------------------------------------------

    def _retry(self, call: Callable[[], object]):
        """``call()`` with a bounded exponential backoff (the F1⁷ pattern);
        re-raises the last exception when every attempt fails."""
        last: Exception = RuntimeError("no fetch attempted")
        for attempt in range(self._fetch_tries):
            try:
                return call()
            except Exception as exc:              # transient 5xx/timeout — retry
                last = exc
                if attempt + 1 < self._fetch_tries:
                    self._sleep(self._fetch_backoff * (2.0 ** attempt))
        raise last

    def _fetch_retry(self, url: str) -> dict:
        return self._retry(lambda: self._fetch(url))

    def _note_fetch_error(self, endpoint: str) -> None:
        self.fetch_errors += 1
        self.fetch_errors_by_endpoint[endpoint] = (
            self.fetch_errors_by_endpoint.get(endpoint, 0) + 1)

    def _count_raise(self, kind: str) -> None:
        self.claims_raised += 1
        self.claims_raised_by_kind[kind] = (
            self.claims_raised_by_kind.get(kind, 0) + 1)

    def _count_resolve(self, kind: str) -> None:
        self.resolutions += 1
        self.resolutions_by_kind[kind] = (
            self.resolutions_by_kind.get(kind, 0) + 1)

    def _schedule(self, date: str) -> List[dict]:
        """The day's games (``[]`` on a fetch failure — degraded, counted)."""
        try:
            data = self._fetch_retry(f"{MLB_API}/schedule?sportId=1&date={date}")
        except Exception:
            self._note_fetch_error("schedule")
            return []
        games: List[dict] = []
        for d in data.get("dates", []):
            games.extend(d.get("games", []))
        return games

    def _standings(self, season: int) -> Dict[int, float]:
        """``team id → win pct`` from the current standings (``{}`` on failure —
        the pct-dependent arms simply raise nothing this poll and retry next)."""
        try:
            data = self._fetch_retry(
                f"{MLB_API}/standings?leagueId=103,104&season={season}")
        except Exception:
            self._note_fetch_error("standings")
            return {}
        table: Dict[int, float] = {}
        for rec in data.get("records", []):
            for tr in rec.get("teamRecords", []):
                team_id = (tr.get("team") or {}).get("id")
                if team_id is not None:
                    table[team_id] = pct_of(int(tr.get("wins", 0)),
                                            int(tr.get("losses", 0)))
        return table

    @staticmethod
    def _consensus_favorite(event: dict) -> Optional[str]:
        """The bookmaker-consensus favorite of one odds event: the team with the
        lower **average decimal price** across the returned books' ``h2h``
        markets. ``None`` on a cross-book tie or a market missing either team."""
        prices: Dict[str, List[float]] = {}
        for bk in event.get("bookmakers", []):
            m = next((m for m in bk.get("markets", [])
                      if m.get("key") == "h2h"), None)
            for o in (m or {}).get("outcomes", []):
                try:
                    prices.setdefault(_const(o.get("name", "")),
                                      []).append(float(o["price"]))
                except (KeyError, TypeError, ValueError):
                    continue
        avg = {t: sum(v) / len(v) for t, v in prices.items() if v}
        home = _const(event.get("home_team", ""))
        away = _const(event.get("away_team", ""))
        if home not in avg or away not in avg or avg[home] == avg[away]:
            return None
        return home if avg[home] < avg[away] else away

    def _odds_table(self) -> Optional[Dict[Tuple[str, str], List[Tuple[datetime, Optional[str]]]]]:
        """One Odds API poll → ``(home, away) → [(commence, favorite|None), …]``
        (a list, so a doubleheader's two games match their own entries). ``None``
        on a fetch failure — the caller retries next poll rather than giving up
        on any pending pick this one."""
        if self._odds_fetch is None:
            return None
        try:
            events = self._retry(self._odds_fetch)
        except Exception:
            self._note_fetch_error("odds")
            return None
        table: Dict[Tuple[str, str], List[Tuple[datetime, Optional[str]]]] = {}
        for ev in events or []:
            start = _iso_dt(str(ev.get("commence_time", "")))
            if start is None:
                continue
            key = (_const(ev.get("home_team", "")), _const(ev.get("away_team", "")))
            table.setdefault(key, []).append((start, self._consensus_favorite(ev)))
        return table

    @staticmethod
    def _odds_lookup(table, home: str, away: str, start: datetime
                     ) -> Tuple[str, Optional[str]]:
        """Match a schedule game to its odds event by team names + nearest
        commence time (≤ 6 h apart — sources disagree by minutes, doubleheaders
        by hours), consuming the entry. Returns ``("ok", favorite)`` /
        ``("tie", None)`` / ``("absent", None)``."""
        cands = table.get((home, away))
        if not cands:
            return "absent", None
        i = min(range(len(cands)),
                key=lambda j: abs((cands[j][0] - start).total_seconds()))
        commence, fav = cands[i]
        if abs((commence - start).total_seconds()) > 6 * 3600:
            return "absent", None
        cands.pop(i)
        return ("tie", None) if fav is None else ("ok", fav)

    # -- phase 1: raise ----------------------------------------------------------

    def _raise_claim(self, game: dict, date: str, kind: str, team: str,
                     game_time: str, diff: Optional[int] = None,
                     cut: Optional[int] = None) -> ResolvingItem:
        pk = _const(game.get("gamePk"))
        claim = PendingGame(pk, date, kind, team, game_time, diff=diff, cut=cut)
        self._claimed.add(claim.key)
        self._pending[claim.key] = claim
        self._count_raise(kind)
        return ResolvingItem(f'(pick_{kind} "{pk}" "{team}")', happened=True)

    def _raise_picks(self, now: datetime) -> List[ResolvingItem]:
        items: List[ResolvingItem] = []
        limit = now + timedelta(hours=self._horizon)
        dates: List[str] = []
        d = now.date()
        while d <= limit.date():
            dates.append(d.isoformat())
            d += timedelta(days=1)
        standings: Optional[Dict[int, float]] = None    # lazy — one fetch per poll
        odds: object = "unfetched"                       # lazy — one Odds API call
        for date in dates:
            for game in self._schedule(date):
                start = _iso_dt(str(game.get("gameDate", "")))
                if start is None or not (now <= start <= limit):
                    continue
                state = str((game.get("status") or {}).get("abstractGameState", ""))
                if state not in ("Preview", ""):
                    continue                            # already live/final — no pick
                if str(game.get("gameType", "R") or "R") != "R":
                    continue                            # regular season only — the
                    # theories (and the P4¹² literature check) are about regular-
                    # season games, not the All-Star/exhibition slate sportId=1
                    # also carries (verified live 2026-07-12: gameType "A")
                pk = str(game.get("gamePk"))
                teams = game.get("teams") or {}
                home = _const(((teams.get("home") or {}).get("team") or {})
                              .get("name", ""))
                away = _const(((teams.get("away") or {}).get("team") or {})
                              .get("name", ""))
                if not home or not away or home == "?" or away == "?":
                    continue
                gt = str(game.get("gameDate", ""))
                for kind in ("naive", "home"):
                    if kind in self._arms and (pk, kind) not in self._claimed:
                        items.append(self._raise_claim(game, date, kind, home, gt))
                if "odds" in self._arms and (pk, "odds") not in self._claimed:
                    if odds == "unfetched":
                        odds = self._odds_table()       # None = fetch failed
                    if odds is not None:
                        status, ofav = self._odds_lookup(odds, home, away, start)
                        if status == "ok":
                            items.append(self._raise_claim(
                                game, date, "odds", ofav, gt))
                        elif status == "tie" or (
                                start - now) < timedelta(hours=2):
                            # A cross-book tie, or a market still unposted close
                            # to first pitch: give up on this game's odds pick —
                            # counted, never silent. An absent market further out
                            # is retried next poll (books post late).
                            self._claimed.add((pk, "odds"))
                            self.odds_skipped += 1
                want_strong = ("strong" in self._arms
                               and (pk, "strong") not in self._claimed)
                want_cal = ("cal" in self._arms and not (
                    {(pk, "fav"), (pk, "dog")} & self._claimed))
                if not (want_strong or want_cal):
                    continue
                if standings is None:
                    standings = self._standings(start.year)
                if not standings:
                    continue                            # retry next poll, counted above
                hid = ((teams.get("home") or {}).get("team") or {}).get("id")
                aid = ((teams.get("away") or {}).get("team") or {}).get("id")
                if hid not in standings or aid not in standings:
                    continue
                fav, dog, diff = favorite_of(home, away,
                                             standings[hid], standings[aid])
                if want_strong:
                    items.append(self._raise_claim(
                        game, date, "strong", fav, gt, diff=diff))
                if want_cal:
                    # Arm B: one direction per game around the learned cut —
                    # the favorite at/above it, the underdog below (RUN_12_LOG B).
                    kind, team = (("fav", fav) if diff >= self._cut
                                  else ("dog", dog))
                    items.append(self._raise_claim(
                        game, date, kind, team, gt, diff=diff, cut=self._cut))
        return items

    # -- phase 2: resolve ---------------------------------------------------------

    @staticmethod
    def _winner_of(game: dict) -> Optional[str]:
        teams = game.get("teams") or {}
        for side in ("home", "away"):
            t = teams.get(side) or {}
            if t.get("isWinner") is True:
                return _const((t.get("team") or {}).get("name", ""))
        return None

    def _resolve_finals(self, now: datetime) -> List[ResolvingItem]:
        items: List[ResolvingItem] = []
        by_date: Dict[str, Optional[Dict[str, dict]]] = {}
        for key in sorted(self._pending):
            claim = self._pending[key]
            if claim.date not in by_date:
                games = self._schedule(claim.date)
                by_date[claim.date] = ({str(g.get("gamePk")): g for g in games}
                                       if games else None)   # None = fetch failed
            table = by_date[claim.date]
            start = _iso_dt(claim.game_time)
            overdue = (start is not None
                       and now > start + timedelta(hours=self._grace))
            if table is None:
                continue                                   # degraded poll — retry
            game = table.get(claim.game_pk)
            if game is None:
                if overdue:                                # vanished from the slate
                    del self._pending[key]
                    self.unresolved_dropped += 1
                continue
            status = game.get("status") or {}
            detailed = str(status.get("detailedState", "")).lower()
            if any(w in detailed for w in _POSTPONED):
                del self._pending[key]                     # counted, never silent
                self.postponed_dropped += 1
                continue
            if str(status.get("abstractGameState", "")) != "Final":
                if overdue:
                    del self._pending[key]
                    self.unresolved_dropped += 1
                continue
            winner = self._winner_of(game)
            if winner is None:
                del self._pending[key]                     # a final with no winner
                self.unresolved_dropped += 1
                continue
            del self._pending[key]
            self._count_resolve(claim.kind)
            claim_egif = f'(win_{claim.kind} "{claim.game_pk}" "{claim.team}")'
            if claim.team == winner:
                items.append(ResolvingItem(claim_egif, happened=True))
            else:
                items.append(ResolvingItem(
                    claim_egif, happened=False,
                    world_egif=(
                        f'(pick_{claim.kind} "{claim.game_pk}" "{claim.team}") '
                        f'~[ {claim_egif} ] '
                        f'(won "{claim.game_pk}" "{winner}")')))
        return items

    # -- the LiveSource shape ------------------------------------------------------

    def fetch(self) -> Sequence[ResolvingItem]:
        now = self._clock()
        items = self._raise_picks(now) + self._resolve_finals(now)
        if self._record and items:
            with open(self._record, "a", encoding="utf-8") as fh:
                fh.write(json.dumps([asdict(i) for i in items]) + "\n")
        return items

    def exhausted(self) -> bool:
        return False                                       # the season plays on

    # -- crash/resume ---------------------------------------------------------------

    def save_state(self, path: str) -> None:
        state = {
            "pending": [asdict(c) for c in self._pending.values()],
            "claimed": sorted(list(k) for k in self._claimed),
            "counters": {"claims_raised": self.claims_raised,
                         "resolutions": self.resolutions,
                         "unresolved_dropped": self.unresolved_dropped,
                         "postponed_dropped": self.postponed_dropped,
                         "odds_skipped": self.odds_skipped,
                         "fetch_errors": self.fetch_errors},
            "claims_raised_by_kind": dict(self.claims_raised_by_kind),
            "resolutions_by_kind": dict(self.resolutions_by_kind),
            "fetch_errors_by_endpoint": dict(self.fetch_errors_by_endpoint),
            # The (possibly recalibrated) knob, so a resume carries the learned
            # cut, not the seed default.
            "params": {"cut": self._cut},
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)

    @classmethod
    def load_state(cls, path: str, **kwargs) -> "SportsSource":
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        src = cls(**kwargs)
        for d in state.get("pending", []):
            c = PendingGame(**d)
            src._pending[c.key] = c
        src._claimed = {tuple(k) for k in state.get("claimed", [])}
        c = state.get("counters", {})
        src.claims_raised = c.get("claims_raised", 0)
        src.resolutions = c.get("resolutions", 0)
        src.unresolved_dropped = c.get("unresolved_dropped", 0)
        src.postponed_dropped = c.get("postponed_dropped", 0)
        src.odds_skipped = c.get("odds_skipped", 0)
        src.fetch_errors = c.get("fetch_errors", 0)
        src.claims_raised_by_kind = dict(state.get("claims_raised_by_kind", {}))
        src.resolutions_by_kind = dict(state.get("resolutions_by_kind", {}))
        src.fetch_errors_by_endpoint = dict(
            state.get("fetch_errors_by_endpoint", {}))
        src._cut = state.get("params", {}).get("cut", src._cut)
        return src


def replay_item_batches(path: str) -> List[List[ResolvingItem]]:
    """Read a ``record_path`` file back into per-poll batches of
    :class:`ResolvingItem` — hand to ``live_runner.ReplaySource`` to re-drive the
    identical trajectory offline (the determinism canary; the same shape as
    ``weather_source.replay_item_batches``, self-contained per source module)."""
    batches: List[List[ResolvingItem]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                batches.append([ResolvingItem(**d) for d in json.loads(line)])
    return batches


__all__ = ["SportsSource", "PendingGame", "ResolvingItem", "pct_of",
           "favorite_of", "replay_item_batches", "ARM_KINDS", "DEFAULT_ARMS",
           "SEED_LAWS", "SEED_LAWS_ODDS", "HELD_LAWS", "HELD_LAWS_ODDS",
           "LAW_NAIVE", "LAW_HOME", "LAW_STRONG", "LAW_FAV", "LAW_DOG",
           "LAW_ODDS"]
