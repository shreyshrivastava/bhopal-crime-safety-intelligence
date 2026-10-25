"""Production entrypoint: reviewed official publications only."""
import streamlit as st
import streamlit.components.v1 as components
from data.official_sources import load_snapshot
from dashboard import generate_dashboard

st.set_page_config(page_title='Bhopal Safety Intelligence', page_icon='🛡️', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>header,footer,#MainMenu{display:none}.block-container{padding:0;max-width:100%}iframe{border:0;width:100%}</style>''', unsafe_allow_html=True)
payload = load_snapshot()
html_content = generate_dashboard(payload)
# Standalone exports are explicit maintenance commands, never request side effects.
components.html(html_content, height=2400, scrolling=True)
