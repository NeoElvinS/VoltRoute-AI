"""Small reusable HTML components."""
import streamlit as st


def header(label, title, sub=""):
    st.markdown(f"<div class='tag'>{label}</div>", unsafe_allow_html=True)
    st.markdown(f"## {title}")
    if sub:
        st.caption(sub)


def cards(items):
    """items: list of (label, value, style) shown as metric cards in one row."""
    cols = st.columns(len(items))
    for c, (l, v, *s) in zip(cols, items):
        c.markdown(f"<div class='card {s[0] if s else ''}'><div class='l'>{l}</div><div class='v'>{v}</div></div>",
                   unsafe_allow_html=True)


def note(text):
    st.markdown(f"<div class='note'>{text}</div>", unsafe_allow_html=True)


def mono(text):
    st.markdown(f"<code class='mono'>{text}</code>", unsafe_allow_html=True)
