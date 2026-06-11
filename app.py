import base64
import datetime
import requests

import plotly.graph_objects as go
import streamlit as st

# 1×1 white pixel as SVG data-URI — used as a layout image so it sits *below*
# flag images in the z-stack (add_shape renders above layout images in Plotly).
_WHITE_RECT = "data:image/svg+xml;base64," + base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
    b'<rect fill="white" width="1" height="1"/></svg>'
).decode()

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

CAPITALS: dict = {
    "PRT": "Lisbon",        "DEU": "Berlin",        "MAR": "Rabat",
    "CHE": "Bern",          "SEN": "Dakar",          "KOR": "Seoul",
    "GHA": "Accra",         "BIH": "Sarajevo",       "ZAF": "Pretoria",
    "QAT": "Doha",          "JOR": "Amman",           "HTI": "Port-au-Prince",
    "FRA": "Paris",         "BRA": "Brasília",        "URY": "Montevideo",
    "NOR": "Oslo",          "MEX": "Mexico City",     "JPN": "Tokyo",
    "EGY": "Cairo",         "CZE": "Prague",          "PAN": "Panama City",
    "IRQ": "Baghdad",       "CUW": "Willemstad",      "NZL": "Wellington",
    "ESP": "Madrid",        "NLD": "Amsterdam",       "BEL": "Brussels",
    "AUT": "Vienna",        "TUR": "Ankara",          "CIV": "Yamoussoukro",
    "ECU": "Quito",         "SCT": "Edinburgh",       "CAN": "Ottawa",
    "UZB": "Tashkent",      "SAU": "Riyadh",          "CPV": "Praia",
    "ARG": "Buenos Aires",  "ENG": "London",          "HRV": "Zagreb",
    "COL": "Bogotá",        "USA": "Washington D.C.", "SWE": "Stockholm",
    "IRN": "Tehran",        "DZA": "Algiers",         "TUN": "Tunis",
    "PRY": "Asunción",      "AUS": "Canberra",        "COD": "Kinshasa",
}

SCORING = [
    ("⚽", "Round of 32",    10),
    ("🎯", "Round of 16",    20),
    ("⚡", "Quarter-finals",  40),
    ("🔥", "Semi-finals",     60),
    ("🏅", "Final",           80),
    ("🏆", "Champions",      100),
    ("👟", "Golden Boot",     25),
]

# ISO codes not in Plotly's built-in world shapes → nearest displayable equivalent
MAP_ISO: dict = {
    "ENG": "GBR",  # England shown as United Kingdom
    "SCT": "GBR",  # Scotland shown as United Kingdom
}

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
    "Curacao": "CUW",                        "New Zealand": "NZL",
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


def _derive_live_data(matches: list) -> tuple:
    """Returns (country_points, country_status) from match results.

    Group stage: no points until a team appears in a R32 fixture (confirmed advance).
    Knockout: winner promoted, loser frozen at that stage's points and marked 'out'.
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

    # Once LAST_32 fixtures exist the group stage is done — remaining picks are eliminated
    if in_knockout:
        all_picks = {iso for d in PEOPLE.values() for _, iso, _, _ in d["countries"]}
        for iso in all_picks:
            if iso not in in_knockout and iso not in stat:
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
COUNTRY_POINTS, COUNTRY_STATUS = _derive_live_data(_matches_data)
for _iso, _bonus in _derive_golden_boot(_scorers_data).items():
    COUNTRY_POINTS[_iso] = COUNTRY_POINTS.get(_iso, 0) + _bonus
_live_ok = bool(_api_key and _matches_data)

iso_index: dict = {}
for person, data in PEOPLE.items():
    for name, iso, flag, flag_code in data["countries"]:
        entry = {"person": person, "country": name, "iso": iso,
                 "flag": flag, "flag_code": flag_code, "color": data["color"]}
        iso_index.setdefault(iso, []).append(entry)
        # Also register under the display ISO so click events on GBR etc. resolve correctly
        if iso in MAP_ISO:
            iso_index.setdefault(MAP_ISO[iso], []).append(entry)

PERSON_ORDER = list(PEOPLE.keys())


def person_total(person: str) -> int:
    return sum(COUNTRY_POINTS.get(iso, 0) for _, iso, _, _ in PEOPLE[person]["countries"])


# ── Map ───────────────────────────────────────────────────────────────────────
# Uses Plotly's built-in ISO-3 world shapes — no GeoJSON file, renders instantly.
# Only WC countries are coloured; the rest show as landcolor.
def make_map(selected_iso=None):
    tc = [data["color"] for data in PEOPLE.values()]

    team_lookup = {}
    plot_rows = {}  # plot_iso → (z, hover_text); later teams overwrite earlier ones
    for person_idx, (person, data) in enumerate(PEOPLE.items(), start=1):
        for name, iso, flag, flag_code in data["countries"]:
            team_lookup[iso] = {
                "person": person, "z": person_idx,
                "name": name, "flag": flag, "flag_code": flag_code,
            }
            plot_iso = MAP_ISO.get(iso, iso)
            plot_rows[plot_iso] = (person_idx, f"<b>{name}</b><br>{person}")

    # For plot ISOs shared by multiple teams (e.g. GBR = England + Scotland),
    # update the hover to credit all teams and add a merged team_lookup entry.
    for plot_iso, picks in iso_index.items():
        if plot_iso in plot_rows and len(picks) > 1:
            nations = "<br>".join(
                f"{p['flag']} {p['country']} → {p['person']}" for p in picks
            )
            plot_rows[plot_iso] = (
                plot_rows[plot_iso][0],
                f"<b>United Kingdom</b><br>{nations}",
            )
            team_lookup[plot_iso] = {
                "person": " & ".join(p["person"] for p in picks),
                "z": plot_rows[plot_iso][0],
                "name": " & ".join(p["country"] for p in picks),
                "flag": " ".join(p["flag"] for p in picks),
                "flag_code": picks[-1]["flag_code"],
            }

    locs = list(plot_rows.keys())
    z_vals = [v[0] for v in plot_rows.values()]
    hover = [v[1] for v in plot_rows.values()]

    # Discrete 4-band colorscale  z=1→Rory  z=2→Dad  z=3→Mum  z=4→Alex
    colorscale = [
        [0.000, tc[0]], [0.249, tc[0]],
        [0.250, tc[1]], [0.499, tc[1]],
        [0.500, tc[2]], [0.749, tc[2]],
        [0.750, tc[3]], [1.000, tc[3]],
    ]

    fig = go.Figure(go.Choropleth(
        locations=locs,
        locationmode="ISO-3",
        z=z_vals,
        zmin=1,
        zmax=4,
        colorscale=colorscale,
        showscale=False,
        text=hover,
        hovertemplate="%{text}<extra></extra>",
        marker_line_color="rgba(255,255,255,0.6)",
        marker_line_width=0.7,
        # Lock opacity so Plotly's selection mode never dims the map
        selected=dict(marker=dict(opacity=1.0)),
        unselected=dict(marker=dict(opacity=1.0)),
    ))

    # ── Selected country: bold border + bottom info card overlay ──────────────
    if selected_iso and selected_iso in team_lookup:
        t = team_lookup[selected_iso]
        team_color = PEOPLE[t["person"].split(" & ")[0]]["color"]
        fig.add_trace(go.Choropleth(
            locations=[selected_iso],
            locationmode="ISO-3",
            z=[1],
            zmin=0, zmax=1,
            colorscale=[[0, team_color], [1, team_color]],
            showscale=False,
            marker_line_color="#1a1a1a",
            marker_line_width=1.5,
            hoverinfo="skip",
            selected=dict(marker=dict(opacity=1.0)),
            unselected=dict(marker=dict(opacity=1.0)),
        ))

        # Info card at the bottom of the map
        picks = iso_index.get(selected_iso, [])
        n = len(picks)
        row_h = 0.09
        card_y1, card_y0 = 0.995, 0.995 - row_h * n

        # Card background — layout image so it sits BELOW flag images in z-order
        # (add_shape renders above layout images; using a white SVG image fixes
        # the "faded flag" issue where the shape was covering the flag at 97% opacity)
        fig.add_layout_image(
            source=_WHITE_RECT,
            x=0.01, y=card_y1,
            xref="paper", yref="paper",
            xanchor="left", yanchor="top",
            sizex=0.98, sizey=card_y1 - card_y0,
            sizing="stretch",
            opacity=1.0,
            layer="above",
        )
        # Thin border around the card (transparent fill — won't cover flags)
        fig.add_shape(
            type="rect",
            x0=0.01, y0=card_y0, x1=0.99, y1=card_y1,
            xref="paper", yref="paper",
            fillcolor="rgba(0,0,0,0)",
            line=dict(color="#d1d5db", width=1),
            layer="above",
        )

        for i, p in enumerate(picks):
            cp = COUNTRY_POINTS.get(p["iso"], 0)
            color = p["color"]
            status = COUNTRY_STATUS.get(p["iso"], "in").upper()
            status_color = "#16a34a" if status == "IN" else "#dc2626"
            row_mid = card_y1 - (i + 0.5) * row_h
            bh = row_h * 0.50          # badge half-height
            by0, by1 = row_mid - bh / 2, row_mid + bh / 2

            # Row divider for multi-pick
            if i > 0:
                fig.add_shape(
                    type="line",
                    x0=0.02, y0=card_y1 - i * row_h,
                    x1=0.98, y1=card_y1 - i * row_h,
                    xref="paper", yref="paper",
                    line=dict(color="#e5e7eb", width=0.5),
                    layer="above",
                )

            # Flag image (full opacity, contained aspect ratio)
            fig.add_layout_image(
                source=f"https://flagcdn.com/w40/{p['flag_code']}.png",
                x=0.04, y=row_mid,
                xref="paper", yref="paper",
                xanchor="center", yanchor="middle",
                sizex=0.048, sizey=row_h * 0.60,
                opacity=1.0,
                sizing="contain",
                layer="above",
            )

            # Country name + capital
            capital = CAPITALS.get(p["iso"], "")
            cap_str = f" ({capital})" if capital else ""
            fig.add_annotation(
                x=0.085, y=row_mid,
                xref="paper", yref="paper",
                text=f"<b>{p['country']}</b>{cap_str}",
                showarrow=False,
                font=dict(size=14, color="#111827", family="Arial"),
                xanchor="left", yanchor="middle",
                bgcolor=None, borderwidth=0,
            )

            # Person badge — coloured box with white text
            fig.add_shape(
                type="rect",
                x0=0.60, y0=by0, x1=0.76, y1=by1,
                xref="paper", yref="paper",
                fillcolor=color, line=dict(width=0),
                layer="above",
            )
            fig.add_annotation(
                x=0.68, y=row_mid,
                xref="paper", yref="paper",
                text=f"<b>{p['person']}</b>",
                showarrow=False,
                font=dict(size=11, color="white", family="Arial"),
                xanchor="center", yanchor="middle",
                bgcolor=None, borderwidth=0,
            )

            # IN / OUT badge
            fig.add_shape(
                type="rect",
                x0=0.78, y0=by0, x1=0.86, y1=by1,
                xref="paper", yref="paper",
                fillcolor=status_color, line=dict(width=0),
                layer="above",
            )
            fig.add_annotation(
                x=0.82, y=row_mid,
                xref="paper", yref="paper",
                text=f"<b>{status}</b>",
                showarrow=False,
                font=dict(size=10, color="white", family="Arial"),
                xanchor="center", yanchor="middle",
                bgcolor=None, borderwidth=0,
            )

            # Points
            fig.add_annotation(
                x=0.89, y=row_mid,
                xref="paper", yref="paper",
                text=f"<b>{cp} pts</b>",
                showarrow=False,
                font=dict(size=14, color=color, family="Arial"),
                xanchor="left", yanchor="middle",
                bgcolor=None, borderwidth=0,
            )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        transition={"duration": 0},
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#b0bec5",
            showocean=True,
            oceancolor="#d6eaf8",
            landcolor="#eceff1",
            showcountries=True,
            countrycolor="#c5cdd6",
            countrywidth=0.4,
            projection_type="equirectangular",
            bgcolor="#d6eaf8",
            lataxis=dict(range=[-90, 90], showgrid=False),
            lonaxis=dict(range=[-180, 180], showgrid=False),
        ),
        paper_bgcolor="#d6eaf8",
        hoverlabel=dict(bgcolor="white", font_size=13),
        uirevision="stable",
    )
    return fig


# ── Session state init ────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.selected_iso = None
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
        # Keep flat bottom so it connects visually to list when expanded
        st.markdown(
            f"<div style='background:{color};color:white;"
            f"border-radius:10px 10px 0 0;padding:14px 10px;"
            f"text-align:center;font-size:15px;font-weight:700;"
            f"letter-spacing:0.3px;box-shadow:0 2px 10px rgba(0,0,0,0.18);'>"
            f"{person}&nbsp;&nbsp;&middot;&nbsp;&nbsp;{total} pts"
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
                status_text = "OUT" if is_out else "IN"
                status_color = "#ef4444" if is_out else "#16a34a"
                status_bg = "#fee2e2" if is_out else "#dcfce7"
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

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── Map ───────────────────────────────────────────────────────────────────────
# Pre-read the chart's pending selection from session_state so selected_iso is
# up-to-date before make_map() is called — avoids a second rerun per click.
_cs = st.session_state.get("map")
if _cs is not None and hasattr(_cs, "selection") and _cs.selection.points:
    _clicked = _cs.selection.points[0].get("location")
    if _clicked and _clicked in iso_index:
        st.session_state.selected_iso = _clicked

st.plotly_chart(
    make_map(selected_iso=st.session_state.selected_iso),
    use_container_width=True,
    on_select="rerun",
    key="map",
    theme=None,
    config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False},
)

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
