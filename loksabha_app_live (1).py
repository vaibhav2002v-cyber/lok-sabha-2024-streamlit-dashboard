import os
import base64
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Lok Sabha 2024 Results", layout="wide", page_icon="🗳️")


st.title("🗳️ Lok Sabha 2024 Election Results Dashboard")

ALLIANCE_COLORS = {"NDA": "#FF9933", "I.N.D.I.A": "#138808", "OTHER": "#808080"}

# ----------------------------------------------------------------------------------
# 1. DB connection
#    Builds an in-memory SQLite database directly from the CSV files checked
#    into this repo (constituencywise_results.csv, constituencywise_details.csv,
#    partywise_results.csv, statewise_results.csv, states.csv). This works
#    identically on your machine and on Streamlit Cloud — no external server,
#    no secrets, no credentials, no separate .db file to upload.
# ----------------------------------------------------------------------------------
from sqlalchemy.pool import StaticPool

# Alliance party lists — used below to compute party_alliance since the raw
# partywise_results.csv doesn't include that column.
INDIA_ALLIANCE_PARTIES = [
    'Indian National Congress - INC', 'Aam Aadmi Party - AAAP',
    'All India Trinamool Congress - AITC', 'Bharat Adivasi Party - BHRTADVSIP',
    'Communist Party of India  (Marxist) - CPI(M)',
    'Communist Party of India  (Marxist-Leninist)  (Liberation) - CPI(ML)(L)',
    'Communist Party of India - CPI', 'Dravida Munnetra Kazhagam - DMK',
    'Indian Union Muslim League - IUML', 'Jammu & Kashmir National Conference - JKN',
    'Jharkhand Mukti Morcha - JMM', 'Kerala Congress - KEC',
    'Marumalarchi Dravida Munnetra Kazhagam - MDMK',
    'Nationalist Congress Party Sharadchandra Pawar - NCPSP',
    'Rashtriya Janata Dal - RJD', 'Rashtriya Loktantrik Party - RLTP',
    'Revolutionary Socialist Party - RSP', 'Samajwadi Party - SP',
    'Shiv Sena (Uddhav Balasaheb Thackrey) - SHSUBT',
    'Viduthalai Chiruthaigal Katchi - VCK',
]
NDA_ALLIANCE_PARTIES = [
    'Bharatiya Janata Party - BJP', 'Telugu Desam - TDP',
    'Janata Dal  (United) - JD(U)', 'Shiv Sena - SHS', 'AJSU Party - AJSUP',
    'Apna Dal (Soneylal) - ADAL', 'Asom Gana Parishad - AGP',
    'Hindustani Awam Morcha (Secular) - HAMS', 'Janasena Party - JnP',
    'Janata Dal  (Secular) - JD(S)', 'Lok Janshakti Party(Ram Vilas) - LJPRV',
    'Nationalist Congress Party - NCP', 'Rashtriya Lok Dal - RLD',
    'Sikkim Krantikari Morcha - SKM',
]


def classify_alliance(party_name):
    if party_name in INDIA_ALLIANCE_PARTIES:
        return "I.N.D.I.A"
    if party_name in NDA_ALLIANCE_PARTIES:
        return "NDA"
    return "OTHER"


@st.cache_resource
def build_engine():
    base_dir = os.path.dirname(__file__)
    # StaticPool keeps the same in-memory SQLite connection alive across calls
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                            poolclass=StaticPool)

    constituencywise_results = pd.read_csv(os.path.join(base_dir, "constituencywise_results.csv"))
    constituencywise_details = pd.read_csv(os.path.join(base_dir, "constituencywise_details.csv"))
    partywise_results = pd.read_csv(os.path.join(base_dir, "partywise_results.csv"))
    statewise_results = pd.read_csv(os.path.join(base_dir, "statewise_results.csv"))
    stats = pd.read_csv(os.path.join(base_dir, "states.csv"))

    # partywise_results.csv has no alliance info — compute it here
    partywise_results["party_alliance"] = partywise_results["Party"].apply(classify_alliance)

    constituencywise_results.to_sql("constituencywise_results", engine, index=False, if_exists="replace")
    constituencywise_details.to_sql("constituencywise_details", engine, index=False, if_exists="replace")
    partywise_results.to_sql("partywise_results", engine, index=False, if_exists="replace")
    statewise_results.to_sql("statewise_results", engine, index=False, if_exists="replace")
    stats.to_sql("stats", engine, index=False, if_exists="replace")

    return engine


try:
    engine = build_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    st.error(f"❌ Database build failed: {e}")
    st.stop()

# ----------------------------------------------------------------------------------
# 2. One cached function per query — mirrors your SQL file 1:1
#    (_engine with a leading underscore tells st.cache_data not to hash it)
# ----------------------------------------------------------------------------------


@st.cache_data(ttl=600)
def get_total_seats(_engine):
    """Q1"""
    df = pd.read_sql("SELECT COUNT(*) AS total_seats FROM constituencywise_results", _engine)
    return int(df.loc[0, "total_seats"])


@st.cache_data(ttl=600)
def get_seats_by_state(_engine):
    """Q2"""
    query = """
        SELECT t3.State, COUNT(t1.`Parliament Constituency`) AS Parliament_seat
        FROM constituencywise_results t1
        JOIN statewise_results t2 ON t1.`Parliament Constituency` = t2.`Parliament Constituency`
        JOIN stats t3 ON t2.`State ID` = t3.`State ID`
        GROUP BY t3.State
        ORDER BY Parliament_seat DESC
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_seats_by_party(_engine):
    """Q3"""
    query = """
        SELECT t1.Party, COUNT(t2.`Parliament Constituency`) AS seats_won
        FROM partywise_results t1
        JOIN constituencywise_results t2 ON t1.`Party ID` = t2.`Party ID`
        GROUP BY t1.Party
        ORDER BY seats_won DESC
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_india_alliance_total(_engine):
    """Q4"""
    query = """
        SELECT SUM(CASE WHEN party_alliance = 'I.N.D.I.A' THEN Won ELSE 0 END) AS india_total
        FROM partywise_results
    """
    df = pd.read_sql(query, _engine)
    return int(df.loc[0, "india_total"] or 0)


@st.cache_data(ttl=600)
def get_india_alliance_breakup(_engine):
    """Q5"""
    query = """
        SELECT Party AS Party_Name, Won AS Seats_Won
        FROM partywise_results
        WHERE party_alliance = 'I.N.D.I.A'
        ORDER BY Seats_Won DESC
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_alliance_totals(_engine):
    """Q7"""
    query = """
        SELECT p.party_alliance, COUNT(cr.`Constituency ID`) AS Seats_Won
        FROM constituencywise_results cr
        JOIN partywise_results p ON cr.`Party ID` = p.`Party ID`
        WHERE p.party_alliance IN ('NDA', 'I.N.D.I.A', 'OTHER')
        GROUP BY p.party_alliance
        ORDER BY Seats_Won DESC
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_constituency_vote_split(_engine, constituency_name):
    """Q8 — parameterized version of your JAIPUR example"""
    query = text("""
        SELECT t1.Candidate, t1.Party, t1.`EVM Votes`, t1.`Postal Votes`,
               t1.`Total Votes`, t2.`Constituency Name`
        FROM constituencywise_details t1
        JOIN constituencywise_results t2 ON t1.`Constituency ID` = t2.`Constituency ID`
        WHERE t2.`Constituency Name` = :constituency_name
        ORDER BY t1.`Total Votes` DESC
    """)
    return pd.read_sql(query, _engine, params={"constituency_name": constituency_name})


@st.cache_data(ttl=600)
def get_party_seats_in_state(_engine, state_name):
    """Q9 — parameterized version of your RAJASTHAN example"""
    query = text("""
        SELECT t2.Party, COUNT(t1.`Constituency ID`) AS seats_won
        FROM constituencywise_results t1
        JOIN partywise_results t2 ON t1.`Party ID` = t2.`Party ID`
        JOIN statewise_results t3 ON t1.`Parliament Constituency` = t3.`Parliament Constituency`
        JOIN stats t4 ON t3.`State ID` = t4.`State ID`
        WHERE t4.State = :state_name
        GROUP BY t2.Party
        ORDER BY seats_won DESC
    """)
    return pd.read_sql(query, _engine, params={"state_name": state_name})


@st.cache_data(ttl=600)
def get_state_list(_engine):
    return pd.read_sql("SELECT DISTINCT State FROM stats ORDER BY State", _engine)["State"].tolist()


@st.cache_data(ttl=600)
def get_constituency_list(_engine):
    return pd.read_sql(
        "SELECT DISTINCT `Constituency Name` FROM constituencywise_results ORDER BY `Constituency Name`",
        _engine,
    )["Constituency Name"].tolist()


@st.cache_data(ttl=600)
def get_alliance_seats_by_state(_engine):
    """Q10"""
    query = """
        SELECT t4.State,
            SUM(CASE WHEN t2.party_alliance = 'NDA' THEN 1 ELSE 0 END) AS NDA_Seats_Won,
            SUM(CASE WHEN t2.party_alliance = 'I.N.D.I.A' THEN 1 ELSE 0 END) AS INDIA_Seats_Won,
            SUM(CASE WHEN t2.party_alliance = 'OTHER' THEN 1 ELSE 0 END) AS OTHER_Seats_Won
        FROM constituencywise_results t1
        JOIN partywise_results t2 ON t1.`Party ID` = t2.`Party ID`
        JOIN statewise_results t3 ON t1.`Parliament Constituency` = t3.`Parliament Constituency`
        JOIN stats t4 ON t3.`State ID` = t4.`State ID`
        WHERE t2.party_alliance IN ('NDA', 'I.N.D.I.A', 'OTHER')
        GROUP BY t4.State
        ORDER BY t4.State
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_top_evm_candidates(_engine, limit=10):
    """Q11a"""
    query = f"""
        SELECT t2.`Constituency Name`, t2.`Constituency ID`, t1.Candidate,
               MAX(t1.`EVM Votes`) AS evm_votes
        FROM constituencywise_details t1
        JOIN constituencywise_results t2 ON t1.`Constituency ID` = t2.`Constituency ID`
        GROUP BY t2.`Constituency Name`, t2.`Constituency ID`, t1.Candidate
        ORDER BY evm_votes DESC
        LIMIT {int(limit)}
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=600)
def get_winner_runnerup(_engine):
    """Q11b"""
    query = """
        WITH RankedCandidates AS (
            SELECT t3.`Constituency ID`, t3.Candidate, t3.Party,
                   t3.`EVM Votes`, t3.`Postal Votes`,
                   t3.`EVM Votes` + t3.`Postal Votes` AS Total_Votes,
                   ROW_NUMBER() OVER (
                       PARTITION BY t3.`Constituency ID`
                       ORDER BY t3.`EVM Votes` + t3.`Postal Votes` DESC
                   ) AS VoteRank
            FROM constituencywise_results t1
            JOIN statewise_results t2 ON t1.`Parliament Constituency` = t2.`Parliament Constituency`
            JOIN constituencywise_details t3 ON t1.`Constituency ID` = t3.`Constituency ID`
        )
        SELECT cr.`Constituency Name`,
            MAX(CASE WHEN rc.VoteRank = 1 THEN rc.Candidate END) AS `Winning Candidate`,
            MAX(CASE WHEN rc.VoteRank = 2 THEN rc.Candidate END) AS `Runnerup Candidate`
        FROM RankedCandidates rc
        JOIN constituencywise_results cr ON rc.`Constituency ID` = cr.`Constituency ID`
        GROUP BY cr.`Constituency Name`
        ORDER BY cr.`Constituency Name`
    """
    return pd.read_sql(query, _engine)


# ----------------------------------------------------------------------------------
# 3. Tabs — call the functions, plot the results
# ----------------------------------------------------------------------------------

import plotly.express as px

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🇮🇳 National Overview", "🏛️ Party & Alliance",
    "🗺️ State Explorer", "📍 Constituency Explorer", "🥇 Winner vs Runner-up",
])

with tab1:
    st.metric("Total Lok Sabha Seats", get_total_seats(engine))
    seats_by_state = get_seats_by_state(engine)
    fig = px.bar(seats_by_state, x="State", y="Parliament_seat", title="Total seats by state")
    fig.update_layout(xaxis_tickangle=-60)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(seats_by_state, use_container_width=True)

with tab2:
    st.subheader("Seats won by party")
    top_n = st.slider("Show top N parties", 5, 50, 15)
    seats_by_party = get_seats_by_party(engine)
    fig_party = px.bar(seats_by_party.head(top_n), x="seats_won", y="Party", orientation="h")
    fig_party.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_party, use_container_width=True)

    st.divider()
    alliance_totals = get_alliance_totals(engine)
    c1, c2 = st.columns(2)
    with c1:
        fig_alliance = px.pie(alliance_totals, names="party_alliance", values="Seats_Won",
                               color="party_alliance", color_discrete_map=ALLIANCE_COLORS)
        st.plotly_chart(fig_alliance, use_container_width=True)
    with c2:
        st.dataframe(alliance_totals, use_container_width=True)

    st.divider()
    st.metric("Total seats won by I.N.D.I.A alliance", get_india_alliance_total(engine))
    st.dataframe(get_india_alliance_breakup(engine), use_container_width=True)

    st.divider()
    alliance_by_state = get_alliance_seats_by_state(engine)
    fig_stacked = px.bar(alliance_by_state, x="State", y=["NDA_Seats_Won", "INDIA_Seats_Won", "OTHER_Seats_Won"],
                          barmode="stack", title="Alliance-wise seats per state")
    fig_stacked.update_layout(xaxis_tickangle=-60)
    st.plotly_chart(fig_stacked, use_container_width=True)

with tab3:
    state_list = get_state_list(engine)
    selected_state = st.selectbox("Select a state", state_list,
                                   index=state_list.index("RAJASTHAN") if "RAJASTHAN" in state_list else 0)
    party_in_state = get_party_seats_in_state(engine, selected_state)
    fig_state = px.bar(party_in_state, x="seats_won", y="Party", orientation="h",
                        title=f"Seats won by party in {selected_state}")
    fig_state.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_state, use_container_width=True)
    st.dataframe(party_in_state, use_container_width=True)

with tab4:
    constituency_list = get_constituency_list(engine)
    default_idx = constituency_list.index("JAIPUR") if "JAIPUR" in constituency_list else 0
    selected_constituency = st.selectbox("Select a constituency", constituency_list, index=default_idx)
    vote_split = get_constituency_vote_split(engine, selected_constituency)
    fig_votes = px.bar(vote_split, x="Candidate", y=["EVM Votes", "Postal Votes"],
                        barmode="stack", title=f"EVM vs Postal votes — {selected_constituency}")
    fig_votes.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_votes, use_container_width=True)
    st.dataframe(vote_split, use_container_width=True)

    st.divider()
    st.subheader("Top 10 candidates by EVM votes (nationwide)")
    st.dataframe(get_top_evm_candidates(engine, 10), use_container_width=True)

with tab5:
    winner_runnerup = get_winner_runnerup(engine)
    search = st.text_input("Search constituency name (optional)")
    if search:
        winner_runnerup = winner_runnerup[
            winner_runnerup["Constituency Name"].str.contains(search, case=False, na=False)
        ]
    st.dataframe(winner_runnerup, use_container_width=True)
