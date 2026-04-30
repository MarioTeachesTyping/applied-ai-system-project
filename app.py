import streamlit as st

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮", layout="wide")

pg = st.navigation([
    st.Page("pages/game.py", title="Guessing Game", icon="🎮"),
    st.Page("pages/ai_debugger.py", title="AI Debugger", icon="🤖"),
])
pg.run()
