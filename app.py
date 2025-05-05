import streamlit as st
import requests

# Load your API key from Streamlit secrets
API_KEY = st.secrets["PHISH_API_KEY"]
BASE = "https://api.phish.net/v5/attendance/username/"

st.title("Phish.net Common Shows")

# Two text inputs for usernames
user1 = st.text_input("Your Phish.net username")
user2 = st.text_input("Friend’s Phish.net username")

if st.button("Find common shows") and user1 and user2:
    def get_shows(u):
        resp = requests.get(f"{BASE}{u}.json", params={"apikey": API_KEY})
        data = resp.json().get("data", [])
        return {item["showdate"] for item in data}

    s1, s2 = get_shows(user1), get_shows(user2)
    common = sorted(s1 & s2)

    if common:
        st.write(f"🎉 You’ve both been to {len(common)} shows:")
        for date in common:
            st.write(date)
    else:
        st.write("No overlap found.")

