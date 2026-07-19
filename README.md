# 🗳️ Lok Sabha 2024 Election Results Dashboard

An interactive Streamlit dashboard for exploring the results of the 2024 Lok Sabha (Indian
General Election) — national overview, party & alliance breakdowns, state-wise and
constituency-wise results, and winner vs runner-up comparisons.

---

## 📌 Project Workflow

This project followed a simple end-to-end data workflow:

1. **Data Transfer to MySQL**
   Raw election result data was loaded and transferred into a MySQL database
   (`loksabha` schema), organized into multiple related tables:
   - `constituencywise_results`
   - `constituencywise_details`
   - `statewise_results`
   - `partywise_results`
   - `stats`

2. **Data Analysis in MySQL (SQL)**
   Once the data was in MySQL, analysis was performed directly using SQL —
   writing queries with joins, aggregations, window functions (`ROW_NUMBER()`),
   and conditional logic (`CASE WHEN`) to answer questions such as:
   - Total seats in the Lok Sabha
   - Seats won by state
   - Seats won by party
   - Alliance-wise seat totals (NDA / I.N.D.I.A / OTHER)
   - Winner vs runner-up per constituency
   - Vote splits (EVM vs Postal) per constituency

3. **Back to Python**
   After validating the analysis logic in SQL, the same queries were brought
   back into Python using **SQLAlchemy** + **Pandas** (`pd.read_sql`), so the
   results could be fetched dynamically and reused inside the application.

4. **Visualization with Streamlit**
   Finally, the analyzed data was visualized using **Streamlit** + **Plotly Express**,
   turning the SQL query results into an interactive, multi-tab dashboard with
   charts, tables, dropdowns, and filters.

**In short:**
`Raw Data → MySQL (transfer + SQL analysis) → Python (SQLAlchemy + Pandas) → Streamlit (visualization)`

---

## 🧱 Tech Stack

| Layer          | Tool/Library                     |
|----------------|-----------------------------------|
| Database       | MySQL                            |
| DB Connector   | SQLAlchemy + PyMySQL             |
| Data Handling  | Pandas                           |
| Visualization  | Plotly Express                   |
| Web App        | Streamlit                        |

---

## 📊 Dashboard Features

The app is organized into 5 tabs:

1. **🇮🇳 National Overview**
   Total Lok Sabha seats + seat distribution by state (bar chart + table).

2. **🏛️ Party & Alliance**
   - Seats won by party (adjustable Top-N slider)
   - Alliance-wise seat share (pie chart)
   - I.N.D.I.A alliance seat breakdown
   - Alliance-wise seats by state (stacked bar chart)

3. **🗺️ State Explorer**
   Party-wise seat breakdown for any selected state.

4. **📍 Constituency Explorer**
   - EVM vs Postal vote split for a selected constituency
   - Top 10 candidates nationwide by EVM votes

5. **🥇 Winner vs Runner-up**
   Searchable table of winning and runner-up candidates per constituency.

The app also includes a **light, faded background image** behind the dashboard
for visual styling, applied via custom CSS.

---

## ⚙️ Setup & Installation

### 1. Install dependencies
```bash
pip install streamlit pandas sqlalchemy pymysql plotly
```

### 2. Configure database credentials
Database credentials are currently set directly inside `loksabha_app_live.py`:
```python
user = "root"
password = "your_password"
host = "localhost"
port = "3306"
database = "loksabha"
```

> ⚠️ For production or shared use, move these into environment variables or
> `.streamlit/secrets.toml` instead of hardcoding them in the script.

### 3. Set up the MySQL database
Make sure MySQL is running locally and the `loksabha` database exists with
the required tables (`constituencywise_results`, `constituencywise_details`,
`statewise_results`, `partywise_results`, `stats`) populated with data.

### 4. Run the app
```bash
streamlit run loksabha_app_live.py
```

The app will open automatically in your browser at:
```
http://localhost:8501
```

---

## 📁 Project Structure

```
loksabha/
│
├── loksabha_app_live.py     # Main Streamlit application
└── README.md                 # Project documentation (this file)
```

---

## 🔮 Possible Future Improvements

- Move DB credentials to `.streamlit/secrets.toml` for better security
- Add caching indicators / loading states for slow queries
- Add year-over-year comparison if historical election data is added
- Deploy to Streamlit Community Cloud or a cloud MySQL instance
- Add authentication for restricted access
