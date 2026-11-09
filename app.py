"""Production entrypoint: reviewed official publications only."""
import streamlit as st
import streamlit.components.v1 as components
from data.official_sources import load_snapshot
from dashboard import generate_dashboard

st.set_page_config(page_title='Bhopal Safety Intelligence', page_icon='🛡️', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>header,footer,#MainMenu,[data-testid=stHeader],[data-testid=stToolbar],[data-testid=stDecoration]{display:none}.block-container{padding:0;max-width:100%}iframe{position:fixed;top:0;left:0;border:0;width:100%;height:calc(100dvh - 40px)!important;display:block;z-index:5}.st-watermark{position:fixed;inset:auto 0 0 0;height:40px;z-index:10;display:flex;align-items:center;padding:0 170px 0 16px;background:#141311;border-top:1px solid rgba(242,239,232,.12);font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#B8B2A7}.st-watermark a{color:#E08A63;text-decoration:none;margin-left:4px}</style>''', unsafe_allow_html=True)
# Community Cloud floats its badge over the bottom-right corner; this strip keeps that area clear of the dashboard.
st.markdown('<div class="st-watermark">Built with <a href="https://streamlit.io" target="_blank" rel="noopener noreferrer">Streamlit</a></div>', unsafe_allow_html=True)
payload = load_snapshot()
html_content = generate_dashboard(payload)
# Standalone exports are explicit maintenance commands, never request side effects.
components.html(html_content, height=900, scrolling=True)
