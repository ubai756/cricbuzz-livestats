import json
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Demo data
# -----------------------------

MATCHES = [
    {
        "league": "IND vs AUS · 2nd ODI",
        "status": "LIVE",
        "teams": "IND vs AUS",
        "score": "IND 268/6 (47.2)",
        "meta": "India batting · 16 balls remaining",
        "venue": "Wankhede Stadium, Mumbai",
    },
    {
        "league": "ENG vs SA · 1st T20I",
        "status": "UPCOMING",
        "teams": "ENG vs SA",
        "score": "Toss at 19:00",
        "meta": "01:42:18 until start",
        "venue": "Lord's, London",
    },
    {
        "league": "WI vs NZ · 3rd Test",
        "status": "LIVE",
        "teams": "WI vs NZ",
        "score": "WI 412 & 104/3 · NZ 371",
        "meta": "Day 4 · Session 2 · WI lead by 145",
        "venue": "Kensington Oval, Barbados",
    },
]

BATTERS = pd.DataFrame(
    [
        ["Shubman Gill", "IND", "1,247", 62.35, 91.8],
        ["Babar Azam", "PAK", "1,189", 59.45, 88.6],
        ["Harry Brook", "ENG", "1,078", 54.18, 94.2],
        ["Travis Head", "AUS", "1,021", 51.05, 103.7],
    ],
    columns=["Player", "Country", "Runs", "Average", "Strike rate"],
)

BOWLERS = pd.DataFrame(
    [
        ["Jasprit Bumrah", "IND", 38, 4.12, 88.4],
        ["Kagiso Rabada", "SA", 34, 4.38, 84.1],
        ["Pat Cummins", "AUS", 31, 4.56, 81.9],
        ["Rashid Khan", "AFG", 29, 5.88, 79.8],
    ],
    columns=["Player", "Country", "Wickets", "Economy", "Impact score"],
)

DEFAULT_PLAYERS = [
    {"Name": "Shubman Gill", "Country": "India", "Role": "Batter", "Format": "ODI", "Status": "Active"},
    {"Name": "Jasprit Bumrah", "Country": "India", "Role": "Bowler", "Format": "All", "Status": "Active"},
    {"Name": "Babar Azam", "Country": "Pakistan", "Role": "Batter", "Format": "ODI", "Status": "Active"},
    {"Name": "Harry Brook", "Country": "England", "Role": "Batter", "Format": "Test", "Status": "Active"},
]

QUERIES = {
    1: {
        "title": "Players who represent India",
        "level": "Beginner",
        "sql": "SELECT full_name, playing_role, batting_style, bowling_style\nFROM players\nWHERE country = 'India';",
    },
    2: {
        "title": "Matches played in the last 30 days",
        "level": "Beginner",
        "sql": "SELECT match_description, team_1, team_2, venue_name, match_date\nFROM matches\nWHERE match_date >= CURRENT_DATE - INTERVAL '30 days'\nORDER BY match_date DESC;",
    },
    3: {
        "title": "Top 10 ODI run scorers",
        "level": "Beginner",
        "sql": "SELECT player_name, total_runs, batting_average, centuries\nFROM player_format_stats\nWHERE format = 'ODI'\nORDER BY total_runs DESC\nLIMIT 10;",
    },
    17: {
        "title": "Does winning the toss give an advantage?",
        "level": "Advanced",
        "sql": "WITH toss_results AS (\n  SELECT toss_winner, winner, toss_decision\n  FROM matches\n  WHERE status = 'completed'\n)\nSELECT toss_decision,\n  COUNT(*) AS matches,\n  ROUND(100.0 * SUM(toss_winner = winner) / COUNT(*), 1) AS win_pct\nFROM toss_results\nGROUP BY toss_decision;",
    },
    18: {
        "title": "Most economical limited-overs bowlers",
        "level": "Advanced",
        "sql": "SELECT player_name, AVG(economy_rate) AS economy,\n       SUM(wickets) AS total_wickets\nFROM bowling_innings\nWHERE format IN ('ODI', 'T20I')\nGROUP BY player_name\nHAVING COUNT(DISTINCT match_id) >= 10\nORDER BY economy ASC;",
    },
    21: {
        "title": "Comprehensive player performance ranking",
        "level": "Advanced",
        "sql": "SELECT player_name, format,\n  (runs_scored * 0.01)\n  + (batting_average * 0.5)\n  + (strike_rate * 0.3)\n  + (wickets_taken * 2) AS weighted_score\nFROM player_format_stats\nORDER BY weighted_score DESC;",
    },
    23: {
        "title": "Recent player form and momentum",
        "level": "Advanced",
        "sql": "WITH recent_form AS (\n  SELECT player_name, runs, strike_rate,\n    ROW_NUMBER() OVER (PARTITION BY player_name ORDER BY match_date DESC) AS rn\n  FROM batting_innings\n)\nSELECT player_name, AVG(runs) AS last_10_avg,\n  AVG(strike_rate) AS recent_strike_rate\nFROM recent_form\nWHERE rn <= 10\nGROUP BY player_name;",
    },
}

# -----------------------------
# Styling
# -----------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --bg: #101419; --panel: #171c23; --muted: #8f99a8; --gold: #ffbf5b; --green: #73d69d; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 75% 0%, rgba(45,62,89,.16), transparent 34%), #101419; color: #f2f3f5; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.045em; }
    [data-testid="stSidebar"] { background: #11161d; border-right: 1px solid rgba(255,255,255,.08); }
    [data-testid="stSidebar"] * { color: #d6dce4; }
    .block-container { padding-top: 2.3rem; padding-bottom: 4rem; max-width: 1450px; }
    .brand { display:flex; align-items:center; gap:10px; margin-bottom: 20px; }
    .brand-mark { display:grid; place-items:center; width:34px; height:34px; border-radius:10px; background:linear-gradient(145deg,#ffd37a,#f29a2c); color:#1b160d; font-weight:800; font-size:18px; }
    .brand-name { font-family:'Space Grotesk'; font-size:18px; font-weight:700; }
    .brand-sub { color:#9b7a44; font-size:8px; font-weight:700; letter-spacing:.22em; }
    .workspace { border:1px solid rgba(255,255,255,.08); border-radius:10px; padding:10px; margin-bottom:20px; background:rgba(255,255,255,.03); }
    .workspace strong, .workspace span { display:block; }
    .workspace strong { font-size:11px; }
    .workspace span { color:#8793a2; font-size:9px; margin-top:3px; }
    .eyebrow { color:#788493; font-size:9px; font-weight:700; letter-spacing:.18em; }
    .subtitle { color:#8f99a8; font-size:11px; margin-top:-8px; }
    .hero { min-height:270px; padding:34px 38px; border-radius:16px; border:1px solid rgba(255,196,92,.17); background:linear-gradient(90deg,rgba(13,19,26,.98),rgba(13,19,26,.78)), url('https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1800&q=85') center/cover; }
    .hero h1 { font-size:50px; line-height:.95; margin:12px 0 16px; }
    .hero h1 span { color:var(--gold); }
    .hero p { color:#a4aeba; max-width:520px; line-height:1.6; font-size:12px; }
    .metric { min-height:125px; border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:16px; background:linear-gradient(135deg,#1c222b,#151a21); }
    .metric-label { color:#8994a2; font-size:10px; }
    .metric-value { font-family:'Space Grotesk'; font-size:27px; font-weight:700; margin-top:4px; }
    .metric-foot { color:#697585; font-size:9px; }
    .trend { color:var(--green); font-size:9px; float:right; }
    .panel { border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:18px; background:linear-gradient(135deg,#1c222b,#151a21); }
    .panel-title { font-size:17px; margin:4px 0 13px; }
    .match-card { border:1px solid rgba(255,255,255,.07); border-left:2px solid #eab24f; border-radius:10px; padding:13px; background:#1a2029; margin-bottom:9px; }
    .match-card strong { font-family:'Space Grotesk'; }
    .match-meta { color:#788493; font-size:9px; border-top:1px solid rgba(255,255,255,.06); margin-top:9px; padding-top:9px; }
    .live { color:var(--green); font-weight:700; font-size:9px; letter-spacing:.1em; }
    .upcoming { color:#7ca3ea; font-weight:700; font-size:9px; letter-spacing:.1em; }
    .pill { display:inline-block; border-radius:99px; padding:4px 8px; background:rgba(255,191,85,.12); color:#ffd078; font-size:9px; }
    .callout { border:1px solid rgba(255,191,85,.14); background:rgba(255,191,85,.05); border-radius:8px; padding:11px; color:#a8b1bd; font-size:10px; }
    .green-text { color:var(--green); }
    .gold-text { color:var(--gold); }
    .footer-note { color:#768290; font-size:9px; margin-top:16px; }
    .stButton > button { border-radius:8px; border:1px solid rgba(255,255,255,.11); background:rgba(255,255,255,.045); color:#d8dfe7; font-size:11px; }
    .stButton > button:hover { border-color:rgba(255,193,90,.35); color:#ffcb70; }
    div[data-testid="stMetric"] { background:#171c23; border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:14px; }
    div[data-testid="stMetricLabel"] { color:#8994a2; }
    div[data-testid="stMetricValue"] { font-family:'Space Grotesk'; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; }
    .stTabs [data-baseweb="tab"] { color:#8994a2; }
    .stTabs [aria-selected="true"] { color:#ffca71; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------

def section_heading(eyebrow: str, title: str, description: str = ""):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><h2 class="panel-title">{title}</h2>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="subtitle">{description}</div>', unsafe_allow_html=True)


def match_card(match: dict):
    status_class = "live" if match["status"] == "LIVE" else "upcoming"
    st.markdown(
        f"""
        <div class="match-card">
          <div><span class="{status_class}">{match['status']}</span><span style='float:right;color:#a1acb9;font-size:10px'>{'LIVE' if match['status']=='LIVE' else '01:42:18'}</span></div>
          <div style='margin-top:10px;color:#a4aeba;font-size:10px'>{match['league']}</div>
          <div style='display:flex;justify-content:space-between;margin-top:8px;font-size:12px'><strong>{match['teams']}</strong><strong>{match['score']}</strong></div>
          <div class="match-meta">{match['meta']} <span style='float:right'>{match['venue']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sql_result():
    return pd.DataFrame(
        [
            ["India", 82, "72.4%"],
            ["Australia", 76, "68.1%"],
            ["England", 69, "61.6%"],
            ["South Africa", 63, "58.9%"],
        ],
        columns=["team_name", "matches_won", "win_percentage"],
    )

# -----------------------------
# Sidebar navigation
# -----------------------------

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">◉</div><div><div class="brand-name">Cricbuzz</div><div class="brand-sub">LIVESTATS</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace"><strong>Analytics workspace</strong><span>Pro plan · synced</span></div>', unsafe_allow_html=True)
    page = st.radio(
        "NAVIGATION",
        ["Overview", "Live matches", "Player stats", "SQL analytics", "Data manager", "Settings"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown('<div class="workspace"><strong>✓ Data synced</strong><span>2 minutes ago · API healthy</span></div>', unsafe_allow_html=True)
    st.caption("Cricbuzz LiveStats · Streamlit demo")

# -----------------------------
# Pages
# -----------------------------

if page == "Overview":
    st.markdown('<div class="eyebrow">WORKSPACE / DASHBOARD</div><h1>Overview</h1><div class="subtitle">Good evening, Ankit. Here is today\'s cricket pulse.</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="hero"><div class="eyebrow" style="color:#d9a54f">✦ REAL-TIME CRICKET INTELLIGENCE</div><h1>Every innings.<br><span>One clear signal.</span></h1><p>Turn live match data into decisions with a single workspace for scores, player form, and SQL-powered analytics.</p></div>', unsafe_allow_html=True)
    st.write("")
    metric_cols = st.columns(4)
    metric_data = [("Total matches tracked", "1,248", "Across 8 formats this season", "↗ 12.8%"), ("Players in database", "3,826", "+146 added this month", "↗ 8.4%"), ("Queries executed", "18.6k", "94% avg. query success", "↗ 2.1%"), ("API health", "99.8%", "Cricbuzz feed availability", "Healthy")]
    for col, (label, value, foot, trend) in zip(metric_cols, metric_data):
        with col:
            st.markdown(f'<div class="metric"><span class="trend">{trend}</span><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-foot">{foot}</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.15, .85])
    with left:
        section_heading("LIVE NOW", "Matches in play")
        for match in MATCHES:
            match_card(match)
    with right:
        section_heading("MOMENTUM INDEX", "Team performance")
        with st.container(border=True):
            st.caption("Win probability trend · last 12 months · all formats")
            trend_df = pd.DataFrame({"Batting efficiency": [38, 45, 42, 62, 54, 72, 68, 87, 80, 94], "Win conversion": [31, 42, 34, 55, 47, 65, 60, 75, 71, 81]})
            st.line_chart(trend_df, height=225)
            st.markdown('<span class="green-text">⚡ India +14.2% this quarter</span>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.15, .85])
    with left:
        section_heading("RANKINGS", "Top performers")
        tab_bat, tab_bowl = st.tabs(["Batting", "Bowling"])
        with tab_bat:
            st.dataframe(BATTERS, use_container_width=True, hide_index=True)
        with tab_bowl:
            st.dataframe(BOWLERS, use_container_width=True, hide_index=True)
    with right:
        section_heading("MATCH INSIGHT", "Toss advantage")
        with st.container(border=True):
            st.markdown('<span class="pill">✦ Q17 · Advanced</span>', unsafe_allow_html=True)
            st.subheader("Does winning the toss actually help?")
            st.progress(0.68, text="Toss winners · 68% conversion")
            st.markdown('<div class="callout"><span class="green-text">✓ Strong signal</span> across 1,248 matches tracked since 2020.</div>', unsafe_allow_html=True)

elif page == "Live matches":
    st.markdown('<div class="eyebrow">WORKSPACE / LIVE MATCHES</div><h1>Live matches</h1><div class="subtitle">Follow every ball, innings, and momentum shift.</div>', unsafe_allow_html=True)
    st.write("")
    st.button("↻ Refresh feeds")
    st.write("")
    live_tab, upcoming_tab, all_tab = st.tabs(["Live · 3", "Upcoming · 5", "All matches · 12"])
    with live_tab:
        for match in MATCHES:
            if match["status"] == "LIVE":
                match_card(match)
    with upcoming_tab:
        match_card(MATCHES[1])
    with all_tab:
        for match in MATCHES:
            match_card(match)
    st.write("")
    section_heading("BALL-BY-BALL", "Live commentary")
    with st.container(border=True):
        commentary = pd.DataFrame(
            [
                ["47.2", "FOUR", "Gill opens the face and guides it past backward point. 50 partnership.", "12s ago"],
                ["47.1", "·", "Good length outside off, defended solidly into the covers.", "31s ago"],
                ["46.6", "2", "Worked away through midwicket. Sharp running between the wickets.", "54s ago"],
            ],
            columns=["Ball", "Outcome", "Commentary", "Updated"],
        )
        st.dataframe(commentary, use_container_width=True, hide_index=True)

elif page == "Player stats":
    st.markdown('<div class="eyebrow">WORKSPACE / PLAYER STATS</div><h1>Top player stats</h1><div class="subtitle">Compare form, output, and efficiency across formats.</div>', unsafe_allow_html=True)
    st.write("")
    format_choice = st.radio("Format", ["TEST", "ODI", "T20I"], horizontal=True, index=1)
    left, right = st.columns([.7, 1.3])
    with left:
        with st.container(border=True):
            st.markdown('<span class="pill">#1 ODI</span>', unsafe_allow_html=True)
            st.markdown('<div style="text-align:center;font-size:45px;margin:18px 0">SG</div>', unsafe_allow_html=True)
            st.subheader("Shubman Gill")
            st.caption("India · Opening batter")
            st.metric("Impact score", "92.4", "+18.4% form")
            st.divider()
            a, b, c = st.columns(3)
            a.metric("Runs", "1,247")
            b.metric("Average", "62.35")
            c.metric("Strike rate", "91.8")
    with right:
        with st.container(border=True):
            section_heading("SEASON TREND", "Runs by month")
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
            runs = [38, 62, 49, 128, 102, 164, 145, 198, 221]
            st.line_chart(pd.DataFrame({"Runs scored": runs}, index=months), height=300)
            st.markdown('<span class="green-text">+24.6% vs last season</span>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns(2)
    with left:
        section_heading("BATTING", "Run leaders")
        st.dataframe(BATTERS, use_container_width=True, hide_index=True)
    with right:
        section_heading("BOWLING", "Wicket leaders")
        st.dataframe(BOWLERS, use_container_width=True, hide_index=True)

elif page == "SQL analytics":
    st.markdown('<div class="eyebrow">WORKSPACE / SQL ANALYTICS</div><h1>SQL analytics lab</h1><div class="subtitle">25 practice queries mapped to real cricket business questions.</div>', unsafe_allow_html=True)
    st.write("")
    query_ids = list(QUERIES.keys())
    selected_id = st.selectbox("Choose a practice question", query_ids, format_func=lambda item: f"Q{item:02d} · {QUERIES[item]['title']}")
    selected = QUERIES[selected_id]
    st.markdown(f'<span class="pill">{selected["level"]}</span>', unsafe_allow_html=True)
    st.subheader(selected["title"])
    st.markdown('<div class="callout">✦ <b>Business context:</b> Translate a real cricket question into a reusable analytical query.</div>', unsafe_allow_html=True)
    sql = st.text_area("SQL editor", selected["sql"], height=220)
    run = st.button("⚡ Run query", type="primary")
    if run:
        st.success("Query executed successfully in 48ms")
        st.dataframe(sql_result(), use_container_width=True, hide_index=True)
    else:
        st.info("Edit the SQL above and click Run query to preview results.")
    with st.expander("Implementation notes"):
        st.markdown("- Beginner queries use SELECT, WHERE, GROUP BY, and ORDER BY.\n- Intermediate queries add JOINs and aggregates.\n- Advanced queries use CTEs, window functions, and weighted scoring.\n- Replace the demo result with a real database call in production.")

elif page == "Data manager":
    st.markdown('<div class="eyebrow">WORKSPACE / DATA MANAGER</div><h1>Player data manager</h1><div class="subtitle">Create, read, update, and delete player records from one clean interface.</div>', unsafe_allow_html=True)
    st.write("")
    if "players" not in st.session_state:
        st.session_state.players = DEFAULT_PLAYERS.copy()
    with st.expander("＋ Add player", expanded=False):
        with st.form("add_player_form"):
            a, b, c, d = st.columns(4)
            name = a.text_input("Full name")
            country = b.text_input("Country")
            role = c.selectbox("Role", ["Batter", "Bowler", "All-rounder", "Wicket-keeper"])
            fmt = d.selectbox("Format", ["Test", "ODI", "T20I", "All"])
            if st.form_submit_button("Create record"):
                if name.strip() and country.strip():
                    st.session_state.players.append({"Name": name.strip(), "Country": country.strip(), "Role": role, "Format": fmt, "Status": "Active"})
                    st.success(f"Created {name.strip()}")
                else:
                    st.error("Name and country are required.")
    search = st.text_input("Search players or countries", placeholder="e.g. India")
    player_df = pd.DataFrame(st.session_state.players)
    if search:
        mask = player_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        player_df = player_df[mask]
    st.dataframe(player_df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(player_df)} visible records · demo changes persist during this session")
    st.markdown('<div class="footer-note">Demo mode: connect a secure backend and database to persist CRUD changes in production.</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="eyebrow">WORKSPACE / SETTINGS</div><h1>Settings</h1><div class="subtitle">Tune your workspace and data refresh preferences.</div>', unsafe_allow_html=True)
    st.write("")
    with st.container(border=True):
        st.subheader("Data refresh")
        st.toggle("Auto-refresh live matches", value=True)
        st.toggle("Refresh completed matches", value=True)
        st.toggle("API error alerts", value=True)
    with st.container(border=True):
        st.subheader("Display preferences")
        st.toggle("Compact table density", value=False)
        st.toggle("Show advanced metrics", value=True)
        st.toggle("Dark broadcast theme", value=True, disabled=True)
    st.write("")
    with st.container(border=True):
        section_heading("CONNECTION STATUS", "Data sources")
        st.success("Cricbuzz Cricket API · REST · Secure token configured")
        st.success("Analytics database · SQLite demo · 18,624 rows indexed")

st.caption(f"Last rendered {datetime.now().strftime('%d %b %Y, %H:%M')} · Cricbuzz LiveStats")
