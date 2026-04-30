import streamlit as st

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮", layout="wide")

pg = st.navigation([
    st.Page("game.py", title="Guessing Game", icon="🎮"),
    st.Page("pages/1_AI_Debugger.py", title="AI Debugger", icon="🤖"),
])
pg.run()
