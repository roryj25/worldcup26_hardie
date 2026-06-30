import datetime
import requests

import streamlit as st

st.set_page_config(
    page_title="World Cup 2026 · The Hardie Family Showdown",
    page_icon="🏆",
    layout="wide",
)

# ── Picks ─────────────────────────────────────────────────────────────────────
PEOPLE = {
    "Rory": {
        "color": "#D94F45",
        "countries": [
            ("Portugal",             "PRT", "🇵🇹", "pt"),
            ("Germany",              "DEU", "🇩🇪", "de"),
            ("Morocco",              "MAR", "🇲🇦", "ma"),
            ("Switzerland",          "CHE", "🇨🇭", "ch"),
            ("Senegal",              "SEN", "🇸🇳", "sn"),
            ("South Korea",          "KOR", "🇰🇷", "kr"),
            ("Ghana",                "GHA", "🇬🇭", "gh"),
            ("Bosnia & Herzegovina", "BIH", "🇧🇦", "ba"),
            ("South Africa",         "ZAF", "🇿🇦", "za"),
            ("Qatar",                "QAT", "🇶🇦", "qa"),
            ("Jordan",               "JOR", "🇯🇴", "jo"),
            ("Haiti",                "HTI", "🇭🇹", "ht"),
        ],
    },
    "Dad": {
        "color": "#F28C28",
        "countries": [
            ("France",      "FRA", "🇫🇷", "fr"),
            ("Brazil",      "BRA", "🇧🇷", "br"),
            ("Uruguay",     "URY", "🇺🇾", "uy"),
            ("Norway",      "NOR", "🇳🇴", "no"),
            ("Mexico",      "MEX", "🇲🇽", "mx"),
            ("Japan",       "JPN", "🇯🇵", "jp"),
            ("Egypt",       "EGY", "🇪🇬", "eg"),
            ("Czechia",     "CZE", "🇨🇿", "cz"),
            ("Panama",      "PAN", "🇵🇦", "pa"),
            ("Iraq",        "IRQ", "🇮🇶", "iq"),
            ("Curaçao",     "CUW", "🇨🇼", "cw"),
            ("New Zealand", "NZL", "🇳🇿", "nz"),
        ],
    },
    "Mum": {
        "color": "#6A4C93",
        "countries": [
            ("Spain",         "ESP", "🇪🇸", "es"),
            ("Netherlands",   "NLD", "🇳🇱", "nl"),
            ("Belgium",       "BEL", "🇧🇪", "be"),
            ("Austria",       "AUT", "🇦🇹", "at"),
            ("Turkey",        "TUR", "🇹🇷", "tr"),
            ("Côte d'Ivoire", "CIV", "🇨🇮", "ci"),
            ("Ecuador",       "ECU", "🇪🇨", "ec"),
            ("Scotland",      "SCT", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "gb-sct"),
            ("Canada",        "CAN", "🇨🇦", "ca"),
            ("Uzbekistan",    "UZB", "🇺🇿", "uz"),
            ("Saudi Arabia",  "SAU", "🇸🇦", "sa"),
            ("Cabo Verde",    "CPV", "🇨🇻", "cv"),
        ],
    },
    "Alex": {
        "color": "#4CAF50",
        "countries": [
            ("Argentina",     "ARG", "🇦🇷", "ar"),
            ("England",       "ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "gb-eng"),
            ("Croatia",       "HRV", "🇭🇷", "hr"),
            ("Colombia",      "COL", "🇨🇴", "co"),
            ("United States", "USA", "🇺🇸", "us"),
            ("Sweden",        "SWE", "🇸🇪", "se"),
            ("Iran",          "IRN", "🇮🇷", "ir"),
            ("Algeria",       "DZA", "🇩🇿", "dz"),
            ("Tunisia",       "TUN", "🇹🇳", "tn"),
            ("Paraguay",      "PRY", "🇵🇾", "py"),
            ("Australia",     "AUS", "🇦🇺", "au"),
            ("DR Congo",      "COD", "🇨🇩", "cd"),
        ],
    },
}

# Populated from live API data below (overwritten at startup each page load)
COUNTRY_POINTS: dict = {}
COUNTRY_STATUS: dict = {}

SCORING = [
    ("⚽", "Round of 32",    10),
    ("🎯", "Round of 16",    20),
    ("⚡", "Quarter-finals",  40),
    ("🔥", "Semi-finals",     60),
    ("🏅", "Final",           80),
    ("🏆", "Champions",      100),
    ("👟", "Golden Boot",     25),
]



# ── Live data from football-data.org ─────────────────────────────────────────
# Free tier · 10 req/min · comp code WC · register at football-data.org/client/register
_FD_BASE = "https://api.football-data.org/v4"
try:
    _api_key: str = st.secrets.get("FOOTBALL_DATA_API_KEY", "")
except Exception:
    _api_key = ""

# Maps football-data.org team names → ISO-3 codes used throughout this app
WC_TEAM_MAP: dict = {
    "Portugal": "PRT",                       "Germany": "DEU",
    "Morocco": "MAR",                        "Switzerland": "CHE",
    "Senegal": "SEN",                        "Korea Republic": "KOR",
    "South Korea": "KOR",                    "Ghana": "GHA",
    "Bosnia and Herzegovina": "BIH",         "Bosnia & Herzegovina": "BIH",
    "Bosnia-Herzegovina": "BIH",
    "South Africa": "ZAF",                   "Qatar": "QAT",
    "Jordan": "JOR",                         "Haiti": "HTI",
    "France": "FRA",                         "Brazil": "BRA",
    "Uruguay": "URY",                        "Norway": "NOR",
    "Mexico": "MEX",                         "Japan": "JPN",
    "Egypt": "EGY",                          "Czech Republic": "CZE",
    "Czechia": "CZE",                        "Panama": "PAN",
    "Iraq": "IRQ",                           "Curaçao": "CUW",
    "Curacao": "CUW",                        "Cura\xc3\xa7ao": "CUW",
    "New Zealand": "NZL",
    "Spain": "ESP",                          "Netherlands": "NLD",
    "Belgium": "BEL",                        "Austria": "AUT",
    "Turkey": "TUR",                         "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV",                  "Ecuador": "ECU",
    "Scotland": "SCT",                       "Canada": "CAN",
    "Uzbekistan": "UZB",                     "Saudi Arabia": "SAU",
    "Cabo Verde": "CPV",                     "Cape Verde": "CPV",
    "Cape Verde Islands": "CPV",
    "Argentina": "ARG",                      "England": "ENG",
    "Croatia": "HRV",                        "Colombia": "COL",
    "United States": "USA",                  "Sweden": "SWE",
    "Iran": "IRN",                           "Algeria": "DZA",
    "Tunisia": "TUN",                        "Paraguay": "PRY",
    "Australia": "AUS",                      "DR Congo": "COD",
    "Congo DR": "COD",                       "Democratic Republic of Congo": "COD",
}

# ISO → flag_code for all 48 picks (used to show opponent flags in fixtures)
_ALL_FLAG_CODES: dict = {
    iso: fc
    for data in PEOPLE.values()
    for _, iso, _, fc in data["countries"]
}

_STAGE_PTS: dict = {
    "LAST_32": 10, "LAST_16": 20, "QUARTER_FINALS": 40,
    "SEMI_FINALS": 60, "FINAL": 80,
}
_STAGE_ORDER = [
    "GROUP_STAGE", "LAST_32", "LAST_16",
    "QUARTER_FINALS", "SEMI_FINALS", "FINAL",
]
_STAGE_LABEL: dict = {
    "GROUP_STAGE": "GS", "LAST_32": "R32", "LAST_16": "R16",
    "QUARTER_FINALS": "QF", "SEMI_FINALS": "SF",
    "THIRD_PLACE": "3rd", "FINAL": "Final",
}


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_wc_matches(api_key: str) -> list:
    if not api_key:
        return []
    try:
        r = requests.get(
            f"{_FD_BASE}/competitions/WC/matches",
            headers={"X-Auth-Token": api_key}, timeout=10,
        )
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_wc_scorers(api_key: str) -> list:
    if not api_key:
        return []
    try:
        r = requests.get(
            f"{_FD_BASE}/competitions/WC/scorers?limit=10",
            headers={"X-Auth-Token": api_key}, timeout=10,
        )
        r.raise_for_status()
        return r.json().get("scorers", [])
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_wc_standings(api_key: str) -> list:
    if not api_key:
        return []
    try:
        r = requests.get(
            f"{_FD_BASE}/competitions/WC/standings",
            headers={"X-Auth-Token": api_key}, timeout=10,
        )
        r.raise_for_status()
        return r.json().get("standings", [])
    except Exception:
        return []


def _derive_provisional_group_pts(standings: list) -> dict:
    """Return {iso: 10} for teams currently in qualifying positions per API group standings.

    Positions 1–2 qualify automatically (if they've played ≥ 1 game).
    Best 8 third-place teams also qualify.
    Applied whenever standings are available, including when some LAST_32
    fixtures already exist (mixed group-stage / knockout state).
    """
    per_group: dict = {}
    for entry in standings:
        if entry.get("type") != "TOTAL":
            continue
        group = entry.get("group", "")
        if group:
            per_group[group] = entry

    pts: dict = {}
    third_place: list = []

    for entry in per_group.values():
        by_pos: dict = {}
        for row in (entry.get("table") or []):
            team_name = (row.get("team") or {}).get("name", "")
            iso = WC_TEAM_MAP.get(team_name)
            if not iso:
                # Try short name fallback
                iso = WC_TEAM_MAP.get((row.get("team") or {}).get("shortName", ""))
            if not iso:
                continue
            team = {
                "iso": iso,
                "played": row.get("playedGames", 0),
                "points": row.get("points", 0),
                "gd": row.get("goalDifference", 0),
                "gf": row.get("goalsFor", 0),
            }
            by_pos.setdefault(row.get("position"), []).append(team)

        # Auto-qualifiers: positions 1 and 2 (only once they've played ≥ 1 game)
        for pos in (1, 2):
            for team in by_pos.get(pos, []):
                if team["played"] > 0:
                    pts[team["iso"]] = 10

        # Third-place pool (only include teams that have played ≥ 1 game)
        if 3 in by_pos:
            for t in by_pos[3]:
                if t["played"] > 0:
                    third_place.append(t)
        elif len(by_pos.get(2, [])) > 1:
            # Two teams tied at pos=2 before their direct match — no pos=3 exists yet.
            # Use the lower-ranked as provisional third-place representative.
            tied = sorted(by_pos[2], key=lambda t: (-t["points"], -t["gd"], -t["gf"]))
            if tied[-1]["played"] > 0:
                third_place.append(tied[-1])

    third_place.sort(key=lambda x: (-x["points"], -x["gd"], -x["gf"]))
    for t in third_place[:8]:
        pts[t["iso"]] = 10
    return pts


def _derive_group_eliminations(standings: list) -> set:
    """Return ISOs definitively eliminated from the group stage.

    A team is only eliminated once its group is fully played (all 4 teams have
    played 3 games). Position-4 teams are out; position-3 teams go into the
    cross-group third-place pool and the bottom 4 of that pool are also out.
    Teams whose group is still in progress are never marked eliminated here.
    """
    per_group: dict = {}
    for entry in standings:
        if entry.get("type") != "TOTAL":
            continue
        group = entry.get("group", "")
        if group:
            per_group[group] = entry

    eliminated: set = set()
    third_pool: list = []

    for entry in per_group.values():
        rows = sorted(entry.get("table") or [], key=lambda r: r.get("position", 0))
        # Skip groups where not all teams have played 3 games yet
        if not all(r.get("playedGames", 0) >= 3 for r in rows):
            continue
        for row in rows:
            iso = WC_TEAM_MAP.get((row.get("team") or {}).get("name", "")) or \
                  WC_TEAM_MAP.get((row.get("team") or {}).get("shortName", ""))
            if not iso:
                continue
            pos = row.get("position", 0)
            if pos == 4:
                eliminated.add(iso)
            elif pos == 3:
                third_pool.append({
                    "iso": iso,
                    "points": row.get("points", 0),
                    "gd": row.get("goalDifference", 0),
                    "gf": row.get("goalsFor", 0),
                })

    # Best 8 third-place advance; the rest are out
    third_pool.sort(key=lambda x: (-x["points"], -x["gd"], -x["gf"]))
    for t in third_pool[8:]:
        eliminated.add(t["iso"])

    return eliminated


def _derive_live_data(matches: list, standings: list = None) -> tuple:
    """Returns (country_points, country_status) from match results.

    Group stage: provisional 10 pts for teams in qualifying positions per standings.
    Teams are only marked 'out' when definitively eliminated (group complete + didn't
    qualify) or when they lose a knockout match. Teams still playing are never 'out'.
    """
    pts: dict = {}
    stat: dict = {}
    in_knockout: set = set()

    for m in matches:
        stage = m.get("stage", "")
        h_name = (m.get("homeTeam") or {}).get("name", "")
        a_name = (m.get("awayTeam") or {}).get("name", "")
        h_iso = WC_TEAM_MAP.get(h_name)
        a_iso = WC_TEAM_MAP.get(a_name)

        # Any R32 fixture (any status) = team confirmed qualified from groups
        if stage == "LAST_32":
            for iso in (h_iso, a_iso):
                if iso:
                    in_knockout.add(iso)
                    pts[iso] = max(pts.get(iso, 0), 10)

        if stage not in _STAGE_PTS or m.get("status") != "FINISHED":
            continue

        winner_side = (m.get("score") or {}).get("winner")
        if not winner_side or winner_side == "DRAW":
            continue

        w_iso = h_iso if winner_side == "HOME_TEAM" else a_iso
        l_iso = a_iso if winner_side == "HOME_TEAM" else h_iso

        if stage == "FINAL":
            if w_iso:
                pts[w_iso] = 100
            if l_iso:
                pts[l_iso] = max(pts.get(l_iso, 0), 80)
                stat[l_iso] = "out"
        else:
            idx = _STAGE_ORDER.index(stage)
            if w_iso and idx + 1 < len(_STAGE_ORDER):
                next_pts = _STAGE_PTS.get(_STAGE_ORDER[idx + 1], _STAGE_PTS[stage])
                pts[w_iso] = max(pts.get(w_iso, 0), next_pts)
            if l_iso:
                pts[l_iso] = max(pts.get(l_iso, 0), _STAGE_PTS[stage])
                stat[l_iso] = "out"

    # Provisional standings — always apply (even when some LAST_32 fixtures exist).
    prov_quals: set = set()
    if standings:
        for iso, p in _derive_provisional_group_pts(standings).items():
            prov_quals.add(iso)
            pts[iso] = max(pts.get(iso, 0), p)
        # Mark only teams whose group is fully played and who definitively didn't qualify.
        for iso in _derive_group_eliminations(standings):
            if iso not in stat:
                stat[iso] = "out"

    return pts, stat


def _derive_golden_boot(scorers: list) -> dict:
    """Returns {iso: 25} if the current top scorer's team is one of our picks."""
    if not scorers:
        return {}
    top = scorers[0]
    iso = WC_TEAM_MAP.get((top.get("team") or {}).get("name", ""))
    all_picks = {i for d in PEOPLE.values() for _, i, _, _ in d["countries"]}
    return {iso: 25} if iso and iso in all_picks else {}


def _get_person_fixtures(matches: list, person_isos: set) -> list:
    """Return live, upcoming (72 h) and recently-finished (24 h) matches for a pick-set."""
    now = datetime.datetime.now(datetime.timezone.utc)
    future = now + datetime.timedelta(hours=72)
    past = now - datetime.timedelta(hours=24)
    out = []
    for m in matches:
        h_iso = WC_TEAM_MAP.get((m.get("homeTeam") or {}).get("name", ""))
        a_iso = WC_TEAM_MAP.get((m.get("awayTeam") or {}).get("name", ""))
        if not (h_iso in person_isos or a_iso in person_isos):
            continue
        mstatus = m.get("status", "")
        try:
            dt = datetime.datetime.fromisoformat(
                m.get("utcDate", "").replace("Z", "+00:00")
            )
        except Exception:
            continue
        if mstatus in ("IN_PLAY", "PAUSED"):
            out.append(m)
        elif mstatus in ("SCHEDULED", "TIMED") and now <= dt <= future:
            out.append(m)
        elif mstatus == "FINISHED" and past <= dt <= now:
            out.append(m)
    return sorted(out, key=lambda x: x.get("utcDate", ""))


# ── Fetch live data and overwrite COUNTRY_POINTS / COUNTRY_STATUS ─────────────
_matches_data = _fetch_wc_matches(_api_key)
_scorers_data = _fetch_wc_scorers(_api_key)
_standings_data = _fetch_wc_standings(_api_key)
COUNTRY_POINTS, COUNTRY_STATUS = _derive_live_data(_matches_data, _standings_data)
for _iso, _bonus in _derive_golden_boot(_scorers_data).items():
    COUNTRY_POINTS[_iso] = COUNTRY_POINTS.get(_iso, 0) + _bonus
_live_ok = bool(_api_key and _matches_data)
# Count confirmed R32 slots. We stay in "group stage" mode (showing PROV labels)
# until all 32 slots are filled — not just when the first R32 match gets scheduled.
_confirmed_r32_isos: set = set()
for _m in _matches_data:
    if _m.get("stage") == "LAST_32":
        for _side in ("homeTeam", "awayTeam"):
            _iso = WC_TEAM_MAP.get((_m.get(_side) or {}).get("name", ""))
            if _iso:
                _confirmed_r32_isos.add(_iso)
_in_group_stage = _live_ok and len(_confirmed_r32_isos) < 32
_has_knockout = any(m.get("stage") == "LAST_32" for m in _matches_data)

def person_total(person: str) -> int:
    return sum(COUNTRY_POINTS.get(iso, 0) for _, iso, _, _ in PEOPLE[person]["countries"])


def _build_bracket_html(matches: list) -> str:
    iso_to_color, iso_to_name, iso_to_fc = {}, {}, {}
    for pdata in PEOPLE.values():
        for name, iso, _, fc in pdata["countries"]:
            iso_to_color[iso] = pdata["color"]
            iso_to_name[iso] = name
            iso_to_fc[iso] = fc

    _SHORT = {
        "BIH": "Bosnia", "USA": "USA", "ZAF": "S. Africa",
        "KOR": "S. Korea", "SAU": "S. Arabia", "NZL": "N. Zealand",
        "CIV": "Ivory Coast", "COD": "Congo DR", "CPV": "Cape Verde",
        "SCT": "Scotland",
    }

    def _isos(m):
        if not m: return None, None
        h = WC_TEAM_MAP.get((m.get("homeTeam") or {}).get("name", ""))
        a = WC_TEAM_MAP.get((m.get("awayTeam") or {}).get("name", ""))
        return h, a

    def _winner_derived(m, h_ov=None, a_ov=None):
        """Winner ISO of a match; team names from API or overridden by derived ISOs."""
        if not m or m.get("status") != "FINISHED": return None
        w = (m.get("score") or {}).get("winner")
        h, a = _isos(m)
        if not h: h = h_ov
        if not a: a = a_ov
        return h if w == "HOME_TEAM" else (a if w == "AWAY_TEAM" else None)

    def _score_str(m):
        if not m: return ""
        ft = ((m.get("score") or {}).get("fullTime") or {})
        h, a = ft.get("home"), ft.get("away")
        return f"{h}–{a}" if h is not None and a is not None else ""

    def _slot(iso, loser=False):
        if not iso:
            return ("<div style='height:30px;background:#1f2937;border-radius:4px;"
                    "display:flex;align-items:center;padding:0 8px;"
                    "font-size:11px;color:#4b5563;font-weight:600;'>TBD</div>")
        color = iso_to_color.get(iso, "#4b5563")
        name = _SHORT.get(iso, iso_to_name.get(iso, iso))
        fc = iso_to_fc.get(iso, "")
        flag = (f"<img src='https://flagcdn.com/w20/{fc}.png' "
                f"style='height:12px;border-radius:1px;margin-right:5px;"
                f"flex-shrink:0;vertical-align:middle;'>") if fc else ""
        if loser:
            return (f"<div style='height:30px;background:#1a2332;border-radius:4px;"
                    f"display:flex;align-items:center;padding:0 8px;"
                    f"font-size:11px;color:#374151;font-weight:600;"
                    f"overflow:hidden;white-space:nowrap;border-left:3px solid #374151;'>"
                    f"{flag}<span style='text-decoration:line-through;opacity:0.45;'>{name}</span></div>")
        return (f"<div style='height:30px;background:{color};border-radius:4px;"
                f"display:flex;align-items:center;padding:0 8px;"
                f"font-size:11px;color:white;font-weight:700;overflow:hidden;"
                f"white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.4);'>"
                f"{flag}{name}</div>")

    def _matchup(m, h_ov=None, a_ov=None):
        """Render a matchup. h_ov/a_ov are derived team ISOs used when the API slot is empty."""
        h, a = _isos(m)
        if not h: h = h_ov
        if not a: a = a_ov
        w = _winner_derived(m, h_ov, a_ov)
        sc = _score_str(m)
        score_html = (f"<div style='height:10px;text-align:center;font-size:9px;"
                      f"color:#6b7280;font-weight:700;line-height:10px;'>{sc}</div>")
        return (f"<div style='display:flex;flex-direction:column;gap:0;"
                f"background:#0f172a;border-radius:5px;padding:3px;'>"
                f"{_slot(h, bool(w and w != h))}"
                f"{score_html}"
                f"{_slot(a, bool(w and w != a))}"
                f"</div>")

    INNER_H = 560

    def _col(slots, label):
        """slots: list of (match, h_ov, a_ov)"""
        items = "".join(f"<div>{_matchup(m, h, a)}</div>" for m, h, a in slots)
        return (
            f"<div style='flex:1;min-width:90px;display:flex;flex-direction:column;'>"
            f"<div style='font-size:9px;font-weight:800;color:#6b7280;"
            f"text-align:center;letter-spacing:1px;text-transform:uppercase;"
            f"padding-bottom:7px;border-bottom:1px solid #1f2937;'>{label}</div>"
            f"<div style='display:flex;flex-direction:column;"
            f"justify-content:space-around;height:{INNER_H}px;'>{items}</div>"
            f"</div>"
        )

    def _pad(lst, n):
        return list(lst) + [None] * max(0, n - len(lst))

    def _by_stage(stage):
        return sorted([m for m in matches if m.get("stage") == stage],
                      key=lambda m: m.get("id", 0))

    def _g(lst, i):
        return lst[i] if i < len(lst) else None

    def _mkey(m):
        h, a = _isos(m)
        return frozenset([h, a]) if h and a else None

    def _find_match(pool, h_iso, a_iso):
        """Return the fixture in pool whose two teams match h_iso/a_iso (either order)."""
        if not h_iso or not a_iso:
            return None
        want = frozenset([h_iso, a_iso])
        for m in pool:
            if _mkey(m) == want:
                return m
        return None

    r32 = _by_stage("LAST_32")
    r16 = _by_stage("LAST_16")
    qf  = _by_stage("QUARTER_FINALS")
    sf  = _by_stage("SEMI_FINALS")
    fin = _by_stage("FINAL")

    # ── Sort R32 into correct bracket positions using the draw ────────────────
    # Sorting by API match ID is unreliable because the schedule interleaves
    # left/right bracket games. We hardcode the known bracket draw order.
    _L_ORDER = [
        frozenset(["DEU","PRY"]), frozenset(["FRA","SWE"]),
        frozenset(["ZAF","CAN"]), frozenset(["NLD","MAR"]),
        frozenset(["PRT","HRV"]), frozenset(["ESP","AUT"]),
        frozenset(["USA","BIH"]), frozenset(["BEL","SEN"]),
    ]
    _R_ORDER = [
        frozenset(["BRA","JPN"]), frozenset(["CIV","NOR"]),
        frozenset(["MEX","ECU"]), frozenset(["ENG","COD"]),
        frozenset(["ARG","CPV"]), frozenset(["AUS","EGY"]),
        frozenset(["CHE","DZA"]), frozenset(["COL","GHA"]),
    ]
    _l_idx = {k: i for i, k in enumerate(_L_ORDER)}
    _r_idx = {k: i for i, k in enumerate(_R_ORDER)}

    l_r32 = _pad(
        sorted([m for m in r32 if _mkey(m) in _l_idx], key=lambda m: _l_idx.get(_mkey(m), 99)),
        8,
    )
    r_r32 = _pad(
        sorted([m for m in r32 if _mkey(m) in _r_idx], key=lambda m: _r_idx.get(_mkey(m), 99)),
        8,
    )

    # ── Build each subsequent round by deriving teams from previous winners ───
    # For each next-round slot i: home = winner of source[2i], away = winner of source[2i+1].
    # The API fixture is located by team-name matching (not ID order) so a mis-ordered
    # schedule can never put the wrong team in the wrong bracket column.

    def _next_slots(source_slots, next_pool):
        result = []
        for i in range(len(source_slots) // 2):
            sh = source_slots[2 * i]
            sa = source_slots[2 * i + 1]
            h_ov = _winner_derived(*(sh or (None, None, None)))
            a_ov = _winner_derived(*(sa or (None, None, None)))
            api_m = _find_match(next_pool, h_ov, a_ov)
            result.append((api_m, h_ov, a_ov))
        return result

    l_r32_slots = [(m, None, None) for m in l_r32]
    l_r16_slots = _next_slots(l_r32_slots, r16)
    l_qf_slots  = _next_slots(l_r16_slots, qf)
    l_sf_slots  = _next_slots(l_qf_slots,  sf)

    r_r32_slots = [(m, None, None) for m in r_r32]
    r_r16_slots = _next_slots(r_r32_slots, r16)
    r_qf_slots  = _next_slots(r_r16_slots, qf)
    r_sf_slots  = _next_slots(r_qf_slots,  sf)

    # Final: derive home/away from SF winners; find API fixture by team matching
    l_sf_win = _winner_derived(*(_g(l_sf_slots, 0) or (None, None, None)))
    r_sf_win = _winner_derived(*(_g(r_sf_slots, 0) or (None, None, None)))
    fin_m = _find_match(fin, l_sf_win, r_sf_win) or _g(fin, 0)
    fin_h, fin_a = _isos(fin_m)
    if not fin_h: fin_h = l_sf_win
    if not fin_a: fin_a = r_sf_win

    # ── Champion ──────────────────────────────────────────────────────────────
    champ = _winner_derived(fin_m, l_sf_win, r_sf_win)
    champ_html = ""
    if champ:
        c = iso_to_color.get(champ, "#6b7280")
        n = iso_to_name.get(champ, champ)
        fc_c = iso_to_fc.get(champ, "")
        fg = (f"<img src='https://flagcdn.com/w20/{fc_c}.png' "
              f"style='height:14px;border-radius:1px;margin-right:5px;'>") if fc_c else ""
        champ_html = (f"<div style='margin-top:10px;background:{c};color:white;"
                      f"border-radius:6px;padding:8px 10px;font-size:12px;"
                      f"font-weight:800;display:flex;align-items:center;"
                      f"justify-content:center;box-shadow:0 2px 12px rgba(0,0,0,0.5);'>"
                      f"🏆 &nbsp;{fg}{n}</div>")

    center = (
        f"<div style='flex:1.1;min-width:110px;display:flex;flex-direction:column;"
        f"align-items:center;justify-content:center;height:{INNER_H + 20}px;padding:0 6px;'>"
        f"<div style='font-size:9px;font-weight:800;color:#6b7280;"
        f"letter-spacing:1px;text-transform:uppercase;padding-bottom:7px;'>Final</div>"
        f"<div style='width:100%;'>{_matchup(fin_m, l_sf_win, r_sf_win)}</div>"
        f"{champ_html}"
        f"</div>"
    )

    gap = "<div style='width:6px;flex-shrink:0;'></div>"

    legend_items = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:5px;margin-right:14px;'>"
        f"<span style='width:12px;height:12px;border-radius:3px;background:{d['color']};"
        f"display:inline-block;box-shadow:0 1px 3px rgba(0,0,0,0.3);'></span>"
        f"<span style='font-size:11px;color:#9ca3af;font-weight:700;'>{p}</span></span>"
        for p, d in PEOPLE.items()
    )

    return (
        f"<div style='background:#0d1117;border-radius:16px;padding:22px 18px 20px;"
        f"margin-top:16px;border:1px solid #1f2937;'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"margin-bottom:16px;flex-wrap:wrap;gap:8px;'>"
        f"<div style='font-size:15px;font-weight:800;color:#f0c040;letter-spacing:2px;'>"
        f"⚽ &nbsp;KNOCKOUT BRACKET</div>"
        f"<div style='display:flex;align-items:center;flex-wrap:wrap;'>{legend_items}</div>"
        f"</div>"
        f"<div style='display:flex;align-items:flex-start;gap:0;width:100%;'>"
        f"{_col(l_r32_slots, 'Round of 32')}{gap}"
        f"{_col(l_r16_slots, 'Round of 16')}{gap}"
        f"{_col(l_qf_slots, 'Quarter-Final')}{gap}"
        f"{_col(l_sf_slots, 'Semi-Final')}{gap}"
        f"{center}{gap}"
        f"{_col(r_sf_slots, 'Semi-Final')}{gap}"
        f"{_col(r_qf_slots, 'Quarter-Final')}{gap}"
        f"{_col(r_r16_slots, 'Round of 16')}{gap}"
        f"{_col(r_r32_slots, 'Round of 32')}"
        f"</div></div>"
    )


# ── Session state init ────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.show_countries = False

# ── Page ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background:linear-gradient(135deg,#0b1e3d 0%,#1a3060 100%);
    border-radius:14px;padding:28px 32px 22px;margin-bottom:18px;
    text-align:center;box-shadow:0 6px 28px rgba(0,0,0,0.28);
">
    <div style="font-size:44px;margin-bottom:4px;">🏆 ⚽ 🏆</div>
    <div style="color:#f0c040;font-size:36px;font-weight:900;letter-spacing:3px;
        text-shadow:0 2px 12px rgba(0,0,0,0.5);line-height:1.1;">WORLD CUP 2026</div>
    <div style="color:#c8d8f0;font-size:19px;font-style:italic;
        margin-top:6px;letter-spacing:0.5px;">The Hardie Family Showdown</div>
</div>
""", unsafe_allow_html=True)

if not _live_ok:
    st.markdown(
        "<div style='background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;"
        "padding:10px 14px;margin-bottom:12px;font-size:13px;color:#92400e;'>"
        "⚠️ <strong>Live data unavailable.</strong> Add your "
        "<code>FOOTBALL_DATA_API_KEY</code> to <code>.streamlit/secrets.toml</code> "
        "to enable live scores, fixtures and top scorers. "
        "Register free at football-data.org/client/register.</div>",
        unsafe_allow_html=True,
    )

# ── Team panels: banners + single toggle + country lists ─────────────────────
st.markdown("""<style>
div[data-testid="stButton"] > button {
    background: #f3f4f6 !important;
    border: 1px solid #e5e7eb !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    padding: 3px 8px !important;
    min-height: 26px !important;
    color: #9ca3af !important;
    font-size: 13px !important;
    line-height: 1 !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    background: #e5e7eb !important;
    color: #374151 !important;
}
div[data-testid="stButton"] > button p {
    font-size: 13px !important;
    line-height: 1 !important;
}
</style>""", unsafe_allow_html=True)

# ── Banners row ───────────────────────────────────────────────────────────────
banner_cols = st.columns(4, gap="small")
for col, (person, data) in zip(banner_cols, PEOPLE.items()):
    with col:
        total = person_total(person)
        color = data["color"]
        prov_note = (
            "<div style='font-size:10px;font-weight:400;opacity:0.82;margin-top:3px;'>"
            "~ incl. provisional pts</div>"
        ) if _in_group_stage else ""
        # Keep flat bottom so it connects visually to list when expanded
        st.markdown(
            f"<div style='background:{color};color:white;"
            f"border-radius:10px 10px 0 0;padding:14px 10px;"
            f"text-align:center;font-size:15px;font-weight:700;"
            f"letter-spacing:0.3px;box-shadow:0 2px 10px rgba(0,0,0,0.18);'>"
            f"{person}&nbsp;&nbsp;&middot;&nbsp;&nbsp;{total} pts"
            f"{prov_note}"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Single toggle button spanning all four banners ────────────────────────────
arrow = "▲  Hide Countries" if st.session_state.show_countries else "▾  Show Countries"
if st.button(arrow, key="countries_toggle", use_container_width=True):
    st.session_state.show_countries = not st.session_state.show_countries
    st.rerun()

# ── Country lists (all four, connected to their banner) ───────────────────────
if st.session_state.show_countries:
    list_cols = st.columns(4, gap="small")
    for col, (person, data) in zip(list_cols, PEOPLE.items()):
        with col:
            rows = ""
            for name, iso, flag, flag_code in data["countries"]:
                cp = COUNTRY_POINTS.get(iso, 0)
                pts_col = data["color"] if cp > 0 else "#9ca3af"
                is_out = COUNTRY_STATUS.get(iso, "in") == "out"
                if is_out:
                    status_text, status_color, status_bg = "OUT", "#ef4444", "#fee2e2"
                elif _in_group_stage and cp > 0:
                    status_text, status_color, status_bg = "PROV", "#b45309", "#fef3c7"
                else:
                    status_text, status_color, status_bg = "IN", "#16a34a", "#dcfce7"
                rows += (
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;padding:7px 10px;"
                    f"border-bottom:1px solid #f3f4f6;font-size:13px;color:#374151;'>"
                    f"<span style='display:flex;align-items:center;gap:5px;flex:1;min-width:0;'>"
                    f"<img src='https://flagcdn.com/w20/{flag_code}.png' "
                    f"style='height:14px;width:auto;display:block;border-radius:2px;flex-shrink:0;'>"
                    f"<span style='font-weight:500;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap;'>{name}</span>"
                    f"<span style='font-size:10px;font-weight:700;color:{status_color};"
                    f"background:{status_bg};padding:1px 5px;border-radius:4px;"
                    f"flex-shrink:0;'>{status_text}</span>"
                    f"</span>"
                    f"<span style='font-weight:700;color:{pts_col};white-space:nowrap;"
                    f"margin-left:8px;'>{cp} pts</span>"
                    f"</div>"
                )
            st.markdown(
                f"<div style='background:white;border:1px solid #e5e7eb;"
                f"border-top:none;border-radius:0 0 10px 10px;overflow:hidden;'>{rows}</div>",
                unsafe_allow_html=True,
            )


# ── Knockout Bracket ─────────────────────────────────────────────────────────
if _live_ok and _has_knockout:
    st.markdown(_build_bracket_html(_matches_data), unsafe_allow_html=True)

# ── Refresh + live data controls ──────────────────────────────────────────────
if _live_ok:
    st.markdown("""<style>
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
    background: #1e3a5f !important;
    border: 1px solid #1e3a5f !important;
    border-top: 1px solid #1e3a5f !important;
    border-radius: 6px !important;
    color: white !important;
    font-size: 12px !important;
    padding: 4px 10px !important;
    min-height: 30px !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
    background: #152d4a !important;
    border-color: #152d4a !important;
}
</style>""", unsafe_allow_html=True)
    _rcol, _tcol = st.columns([1, 6])
    with _rcol:
        if st.button("🔄 Refresh", key="refresh_data", use_container_width=True):
            _fetch_wc_matches.clear()
            _fetch_wc_scorers.clear()
            _fetch_wc_standings.clear()
            st.rerun()
    with _tcol:
        st.markdown(
            "<p style='margin:0;padding-top:5px;color:#9ca3af;font-size:12px;'>"
            "Live data: football-data.org · auto-refreshes every 5 min</p>",
            unsafe_allow_html=True,
        )

# ── Upcoming fixtures ─────────────────────────────────────────────────────────
if _live_ok:
    _fixture_panels = []
    for person, data in PEOPLE.items():
        color = data["color"]
        person_isos = {iso for _, iso, _, _ in data["countries"]}
        person_matches = _get_person_fixtures(_matches_data, person_isos)
        if not person_matches:
            continue
        rows_html = ""
        for m in person_matches:
            h_name = (m.get("homeTeam") or {}).get("name", "—")
            a_name = (m.get("awayTeam") or {}).get("name", "—")
            h_iso = WC_TEAM_MAP.get(h_name, "")
            a_iso = WC_TEAM_MAP.get(a_name, "")
            h_fc = _ALL_FLAG_CODES.get(h_iso, "")
            a_fc = _ALL_FLAG_CODES.get(a_iso, "")
            h_flag = (f"<img src='https://flagcdn.com/w20/{h_fc}.png' "
                      f"style='height:13px;border-radius:2px;vertical-align:middle;"
                      f"margin-right:3px;'>") if h_fc else ""
            a_flag = (f"<img src='https://flagcdn.com/w20/{a_fc}.png' "
                      f"style='height:13px;border-radius:2px;vertical-align:middle;"
                      f"margin-right:3px;'>") if a_fc else ""
            h_bold = "font-weight:700;" if h_iso in person_isos else ""
            a_bold = "font-weight:700;" if a_iso in person_isos else ""
            mstatus = m.get("status", "")
            score_obj = m.get("score") or {}
            ft = score_obj.get("fullTime") or {}
            ht = score_obj.get("halfTime") or {}
            h_score = ft.get("home") if ft.get("home") is not None else ht.get("home")
            a_score = ft.get("away") if ft.get("away") is not None else ht.get("away")
            try:
                _bst = datetime.timezone(datetime.timedelta(hours=1))
                dt = datetime.datetime.fromisoformat(
                    m.get("utcDate", "").replace("Z", "+00:00")
                ).astimezone(_bst)
                date_str = dt.strftime("%d %b %H:%M BST")
            except Exception:
                date_str = ""
            stage_raw = m.get("stage", "")
            group_raw = m.get("group") or ""
            if group_raw:
                stage_lbl = group_raw.replace("GROUP_STAGE_", "Grp ").replace("_", " ")
            else:
                stage_lbl = _STAGE_LABEL.get(stage_raw, stage_raw)

            if mstatus in ("IN_PLAY", "PAUSED"):
                s_badge = ("<span style='background:#dc2626;color:white;"
                           "font-size:9px;font-weight:700;padding:1px 5px;"
                           "border-radius:3px;'>● LIVE</span> ")
                score_txt = f"{h_score}–{a_score}" if h_score is not None else ""
            elif mstatus == "FINISHED":
                if h_score is not None and a_score is not None:
                    own_won = ((h_iso in person_isos and h_score > a_score) or
                               (a_iso in person_isos and a_score > h_score))
                    own_lost = ((h_iso in person_isos and h_score < a_score) or
                                (a_iso in person_isos and a_score < h_score))
                    badge_icon = "✅" if own_won else ("❌" if own_lost else "🤝")
                    score_txt = f"{h_score}–{a_score}"
                else:
                    badge_icon = "✅"
                    score_txt = ""
                s_badge = f"<span style='font-size:11px;'>{badge_icon}</span> "
            else:
                s_badge = (f"<span style='color:#6b7280;font-size:10px;'>{date_str}</span> ")
                score_txt = ""

            rows_html += (
                f"<div style='display:flex;align-items:center;gap:6px;"
                f"padding:6px 10px;border-bottom:1px solid #f3f4f6;font-size:12px;'>"
                f"<span style='color:#9ca3af;font-size:9px;min-width:26px;flex-shrink:0;'>"
                f"{stage_lbl}</span>"
                f"<span style='{h_bold}flex:1;overflow:hidden;text-overflow:ellipsis;"
                f"white-space:nowrap;'>{h_flag}{h_name}</span>"
                f"<span style='color:#9ca3af;font-size:10px;flex-shrink:0;padding:0 2px;'>vs</span>"
                f"<span style='{a_bold}flex:1;overflow:hidden;text-overflow:ellipsis;"
                f"white-space:nowrap;text-align:right;'>{a_name}{a_flag}</span>"
                f"<span style='display:flex;align-items:center;gap:3px;flex-shrink:0;"
                f"min-width:60px;justify-content:flex-end;'>"
                f"{s_badge}"
                f"<span style='font-weight:700;color:#1a3a6b;font-size:12px;'>{score_txt}</span>"
                f"</span></div>"
            )

        if rows_html:
            _fixture_panels.append(
                f"<div style='min-width:220px;flex:1 1 220px;'>"
                f"<div style='background:{color};color:white;font-size:11px;"
                f"font-weight:700;padding:4px 10px;border-radius:6px 6px 0 0;"
                f"letter-spacing:0.5px;'>{person}</div>"
                f"<div style='background:white;border:1px solid #e5e7eb;"
                f"border-top:none;border-radius:0 0 6px 6px;overflow:hidden;'>"
                f"{rows_html}</div></div>"
            )

    if _fixture_panels:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:white;border-radius:12px;"
            f"box-shadow:0 2px 16px rgba(0,0,0,0.09);border:1px solid #e5e7eb;"
            f"overflow:hidden;'>"
            f"<div style='background:linear-gradient(135deg,#0b1e3d,#1a3060);"
            f"padding:11px 18px;display:flex;align-items:center;gap:10px;'>"
            f"<span style='font-size:17px;'>📅</span>"
            f"<span style='color:#f0c040;font-weight:800;font-size:15px;"
            f"letter-spacing:2px;text-transform:uppercase;'>Fixtures (Next 72 hours) </span></div>"
            f"<div style='padding:12px;display:flex;flex-wrap:wrap;gap:8px;'>"
            f"{''.join(_fixture_panels)}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

# ── Top 5 scorers ─────────────────────────────────────────────────────────────
if _live_ok and _scorers_data:
    top5 = _scorers_data[:5]
    _all_pick_isos = {iso for d in PEOPLE.values() for _, iso, _, _ in d["countries"]}
    scorer_rows_html = ""
    for rank, s in enumerate(top5, 1):
        p_name = (s.get("player") or {}).get("name", "—")
        t_name = (s.get("team") or {}).get("name", "—")
        goals = s.get("goals") or s.get("numberOfGoals") or 0
        t_iso = WC_TEAM_MAP.get(t_name, "")
        t_fc = _ALL_FLAG_CODES.get(t_iso, "")
        flag_html = (f"<img src='https://flagcdn.com/w20/{t_fc}.png' "
                     f"style='height:13px;border-radius:2px;vertical-align:middle;"
                     f"margin-right:4px;'>") if t_fc else ""
        picker_html = ""
        if t_iso and t_iso in _all_pick_isos:
            for person, pdata in PEOPLE.items():
                if any(iso == t_iso for _, iso, _, _ in pdata["countries"]):
                    picker_html = (
                        f"<span style='font-size:9px;font-weight:700;color:white;"
                        f"background:{pdata['color']};padding:1px 5px;"
                        f"border-radius:3px;margin-left:4px;'>{person}</span>"
                    )
                    break
        row_bg = "background:#fffbeb;" if rank == 1 else ""
        boot_icon = "👟" if rank == 1 else f"{rank}."
        scorer_rows_html += (
            f"<div style='display:flex;align-items:center;gap:8px;padding:8px 14px;"
            f"border-bottom:1px solid #f3f4f6;{row_bg}'>"
            f"<span style='font-size:13px;min-width:22px;flex-shrink:0;'>{boot_icon}</span>"
            f"<span style='font-size:13px;font-weight:700;color:#111827;flex:1;'>{p_name}</span>"
            f"<span style='font-size:12px;color:#6b7280;display:flex;align-items:center;'>"
            f"{flag_html}{t_name}</span>"
            f"{picker_html}"
            f"<span style='font-size:15px;font-weight:900;color:#1a3a6b;"
            f"min-width:36px;text-align:right;'>{goals}⚽</span>"
            f"</div>"
        )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='background:white;border-radius:12px;"
        f"box-shadow:0 2px 16px rgba(0,0,0,0.09);border:1px solid #e5e7eb;"
        f"overflow:hidden;'>"
        f"<div style='background:linear-gradient(135deg,#0b1e3d,#1a3060);"
        f"padding:11px 18px;display:flex;align-items:center;gap:10px;'>"
        f"<span style='font-size:17px;'>👟</span>"
        f"<span style='color:#f0c040;font-weight:800;font-size:15px;"
        f"letter-spacing:2px;text-transform:uppercase;'>Top Scorers</span></div>"
        f"{scorer_rows_html}</div>",
        unsafe_allow_html=True,
    )

# ── How It Works ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
scoring_items_html = ""
for emoji, stage, pts in SCORING:
    scoring_items_html += (
        f"<div style='flex:1 1 120px;display:flex;justify-content:space-between;"
        f"align-items:center;padding:7px 12px;border-radius:7px;"
        f"background:#f8fafc;border:1px solid #eef0f3;'>"
        f"<span style='color:#374151;font-size:13px;font-weight:600;white-space:nowrap;'>"
        f"{emoji}&nbsp;{stage}</span>"
        f"<span style='font-weight:900;color:#1a3a6b;font-size:15px;"
        f"background:#e8edf7;padding:2px 8px;border-radius:5px;margin-left:8px;'>{pts}</span>"
        f"</div>"
    )
st.markdown(
    f"<div style='background:white;border-radius:12px;"
    f"box-shadow:0 2px 16px rgba(0,0,0,0.09);border:1px solid #e5e7eb;overflow:hidden;'>"
    f"<div style='background:linear-gradient(135deg,#0b1e3d,#1a3060);"
    f"padding:11px 18px;display:flex;align-items:center;gap:10px;'>"
    f"<span style='font-size:17px;'>📋</span>"
    f"<span style='color:#f0c040;font-weight:800;font-size:15px;"
    f"letter-spacing:2px;text-transform:uppercase;'>How It Works</span></div>"
    f"<div style='padding:12px 18px;display:flex;align-items:center;flex-wrap:wrap;gap:10px;'>"
    f"<p style='color:#4b5563;font-size:13px;line-height:1.6;margin:0;flex:1 1 260px;'>"
    f"Each player picks <strong>12 national teams</strong>. Points go to whoever's teams "
    f"advance furthest — highest total <strong>wins the Hardie Family Showdown!</strong> "
    f"<em>Points for furthest stage reached only — they don't stack.</em></p>"
    f"<div style='flex:2 1 400px;display:flex;flex-wrap:wrap;gap:6px;'>"
    f"{scoring_items_html}</div></div></div>",
    unsafe_allow_html=True,
)

