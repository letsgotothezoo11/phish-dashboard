#############################################
# Phish.net Common Shows Dashboard (app.py) #
#############################################

# ─── IMPORTS ───────────────────────────────────────────────────────────────────
import streamlit as st         # Main Streamlit library for UI
import requests                # For HTTP API calls
import pandas as pd            # For DataFrame manipulation
from st_aggrid import AgGrid, GridOptionsBuilder  
                              # For interactive, sortable tables with HTML renderers

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
# Load your Phish.net API key from Streamlit’s secure Secrets store
API_KEY     = st.secrets["PHISH_API_KEY"]
# Base endpoints for attendance and show details
BASE_ATTEND = "https://api.phish.net/v5/attendance/username/"
BASE_SHOW   = "https://api.phish.net/v5/shows/showdate/"

# ─── PAGE HEADER ─────────────────────────────────────────────────────────────────
st.title("Phish.net Common Shows")  # Large page title

# Two columns for username inputs
col1, col2 = st.columns(2)
with col1:
    # Input box for first user’s username
    user1 = st.text_input("Your Phish.net username")
with col2:
    # Input box for friend’s username
    user2 = st.text_input("Friend’s Phish.net username")

# ─── BUTTON ACTION ───────────────────────────────────────────────────────────────
# When the button is clicked, fetch data and render metrics + tabs
if st.button("Find common shows"):

    # 1) VALIDATION: ensure both fields are filled
    if not user1 or not user2:
        st.error("Please enter both usernames.")
        st.stop()  # Halt execution if validation fails

    # 2) FETCH ATTENDANCE: helper function to get show dates + count
    def get_attendance(username: str):
        """
        Calls Phish.net attendance API for a given username,
        returns (list_of_dates, total_count).
        """
        resp = requests.get(
            f"{BASE_ATTEND}{username}.json",
            params={"apikey": API_KEY}
        )
        resp.raise_for_status()                        # Raise on HTTP error
        data = resp.json().get("data", [])             # Safely grab "data" list
        dates = [item["showdate"] for item in data]    # Extract showdate strings
        return dates, len(dates)

    # Fetch each user’s attendance
    dates1, A1 = get_attendance(user1)  # A1 = total shows for user1
    dates2, A2 = get_attendance(user2)  # A2 = total shows for user2

    # 3) INTERSECT & CALCULATE METRICS
    common = sorted(set(dates1) & set(dates2))  # Dates both users attended
    B   = len(common)                           # Common shows count
    C1  = (100 * B / A1) if A1 else 0           # % of user1’s shows with user2
    C2  = (100 * B / A2) if A2 else 0           # % of user2’s shows with user1

       # ─── METRICS ROW (fixed-size, CSS-styled boxes) ────────────────────────────
    st.markdown(f"""
    <style>
      /* … your existing CSS … */
      .metrics-container {{ text-align:center; margin-bottom:30px; }}
      .metric-box {{ display:inline-block; width:220px; height:220px; background:#f5f5f5; border:2px gray; padding:10px; box-sizing:border-box; vertical-align:top; margin:0 15px; }}
      .metric-box h2 {{ font-size:1em; margin:0 0 5px 0; text-align:left; color:black; }}
      .metric-box .value {{ font-size:3em; margin:0; text-align:center; color:black; }}
      .metric-box .caption {{ font-size:1em; margin:5px 0 0 0; text-align:center; color:black; }}
      .metric-center {{ display:inline-block; vertical-align:top; margin:0 15px; text-align:center; }}
      .metric-center h2 {{ font-size:1em; margin:0 0 5px 0; color:black; }}
      .metric-center .value {{ font-size:5em; margin:0; color:blue; }}
    </style>
    <div class="metrics-container">
      <!-- Left box -->
      <div class="metric-box">
        <h2>How many shows {user1} has been to:</h2>
        <p class="value">{A1}</p>
        <p class="caption">{C1:.1f}% of shows with {user2}</p>
      </div>
      <!-- Center box -->
      <div class="metric-center">
        <h2>Shows Together</h2>
        <p class="value">{B}</p>
      </div>
      <!-- Right box -->
      <div class="metric-box">
        <h2>How many shows {user2} has been to:</h2>
        <p class="value">{A2}</p>
        <p class="caption">{C2:.1f}% of shows with {user1}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── DATA LOADING SPINNER & ROW-BUILDING ───────────────────────────────────
    with st.spinner("More data loading, this could take a few minutes if you've been to a lot of shows 🐠🤘"):
        # Build rows for Shows Together
        rows_common = []
        for date in common:
            # 1) Show details
            show_resp = requests.get(f"{BASE_SHOW}{date}.json", params={"apikey": API_KEY})
            show_resp.raise_for_status()
            show = show_resp.json().get("data", [{}])[0]
            venue = show.get("venue", "Unknown venue")
            loc   = show.get("location", "")

            # 2) Setlist permalink → correct URL
            sl_resp = requests.get(f"https://api.phish.net/v5/setlists/showdate/{date}.json",
                                   params={"apikey": API_KEY})
            sl_resp.raise_for_status()
            sl_data = sl_resp.json().get("data", [])
            permalink = sl_data[0].get("permalink", "") if sl_data else ""
            slug = permalink[:-5] if permalink.endswith(".html") else permalink
            url = permalink if permalink.startswith("http") else f"https://phish.net/setlists/{slug}.html"

            rows_common.append({
                "date":     date,
                "location": f"{venue}, {loc}",
                "url":      url
            })

        # Build rows for Shows Apart
        apart_dates = sorted(set(dates1).symmetric_difference(set(dates2)))
        rows_apart = []
        for date in apart_dates:
            attendee = user1 if date in dates1 else user2

            show_resp = requests.get(f"{BASE_SHOW}{date}.json", params={"apikey": API_KEY})
            show_resp.raise_for_status()
            show = show_resp.json().get("data", [{}])[0]
            venue = show.get("venue", "Unknown venue")
            loc   = show.get("location", "")

            sl_resp = requests.get(f"https://api.phish.net/v5/setlists/showdate/{date}.json",
                                   params={"apikey": API_KEY})
            sl_resp.raise_for_status()
            sl_data = sl_resp.json().get("data", [])
            permalink = sl_data[0].get("permalink", "") if sl_data else ""
            slug = permalink[:-5] if permalink.endswith(".html") else permalink
            url = permalink if permalink.startswith("http") else f"https://phish.net/setlists/{slug}.html"

            rows_apart.append({
                "user":     attendee,
                "date":     date,
                "location": f"{venue}, {loc}",
                "url":      url
            })
    # ─── END SPINNER ─────────────────────────────────────────────────────────────

    # ─── TABS RENDERING (unchanged) ─────────────────────────────────────────────
    tabs = st.tabs(["Shows Together", "Songs Together", "Shows Apart"])

    with tabs[0]:
        st.header("Shows Together")
        if rows_common:
            md = "| Date | Location |\n|---|---|\n"
            for r in rows_common:
                md += f"| [{r['date']}]({r['url']}) | {r['location']} |\n"
            st.markdown(md, unsafe_allow_html=True)
        else:
            st.info("You have no shows in common.")

    with tabs[1]:
        st.header("Songs Together")
        st.info("🎶 Songs Together page requested! A project for another day.")

    with tabs[2]:
        st.header("Shows Apart")

        if rows_apart:
            # Build a Markdown table with a “User” column,
            # bolding user1’s name to distinguish them.
            md = "| User | Date | Location |\n|---|---|---|\n"
            for r in rows_apart:
                # Bold user1’s name, leave user2 normal
                user_display = f"**{r['user']}**" if r["user"] == user1 else r["user"]
                # Make date a clickable link if URL exists
                date_link = f"[{r['date']}]({r['url']})" if r["url"] else r["date"]
                md += f"| {user_display} | {date_link} | {r['location']} |\n"

            st.markdown(md, unsafe_allow_html=True)
        else:
            st.info("Neither of you has any unique shows.")
    
