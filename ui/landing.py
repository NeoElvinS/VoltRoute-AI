"""Landing page module for VoltRoute AI with hero section and allocation sequence."""
import random
import streamlit as st
import streamlit.components.v1 as components
from ui.dashboard import get_result, default_params

# ==============================================================================
# LANDING PAGE CONTENT (EDITABLE)
# ==============================================================================
# Modify the text, headings, badges, and button labels below to update the landing page.

HERO_TITLE = "VoltRoute AI"
HERO_DESCRIPTION = "An intelligent agent that determines optimal locations for EV charging stations."

BUTTON_RUN_LABEL = "RUN AI ALLOCATION"
BUTTON_EXPLORE_LABEL = "EXPLORE SYSTEM"

# ==============================================================================
# 3D HERO VISUAL (LOCKED)
# ==============================================================================
# The isometric 3D visual below is locked. Do not modify objects, labels, colors,
# animations, or positioning.

def city_svg():
    R, e, parts = random.Random(5), [0, 90, 230, 370, 510, 600], []
    for k in e[1:5]:
        parts.append(f"<rect x='{k-9}' y='0' width='18' height='600' fill='#CFCABB'/><rect x='0' y='{k-9}' width='600' height='18' fill='#CFCABB'/>")
        parts.append(f"<line x1='{k}' y1='0' x2='{k}' y2='600' stroke='#F6F2E7' stroke-dasharray='6 6'/><line x1='0' y1='{k}' x2='600' y2='{k}' stroke='#F6F2E7' stroke-dasharray='6 6'/>")
    for a in range(5):
        for b in range(5):
            x0, x1, y0, y1 = e[a] + 16, e[a + 1] - 16, e[b] + 16, e[b + 1] - 16
            if R.random() < .15:
                parts.append(f"<rect x='{x0}' y='{y0}' width='{x1-x0}' height='{y1-y0}' fill='#C9DFA0' opacity='.7'/>")
                continue
            for _ in range(R.randint(2, 4)):
                w, h = R.randint(20, 46), R.randint(20, 46)
                x, y = R.randint(x0, max(x0, x1 - w)), R.randint(y0, max(y0, y1 - h))
                c = R.choice(["#E4DFD0", "#D6D2C4", "#EDE8D8", "#BFD1B4"])
                parts.append(f"<rect x='{x+7}' y='{y+7}' width='{w}' height='{h}' fill='#23272A' opacity='.22'/>"
                             f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{c}' stroke='#8C8C84' stroke-width='.8'/>"
                             f"<rect x='{x+4}' y='{y+4}' width='{w-8}' height='{h-8}' fill='none' stroke='#8C8C84' stroke-width='.4'/>")
    for x, y, r in ((150, 150, 60), (440, 190, 72), (300, 430, 58), (110, 470, 44)):
        parts.append(f"<circle cx='{x}' cy='{y}' r='{r}' fill='#D9822B' opacity='.28'/><circle cx='{x}' cy='{y}' r='{r}' fill='none' stroke='#D9822B' stroke-dasharray='4 4'/>")
    sel = [(150, 150), (440, 190), (300, 430), (110, 470), (500, 460)]
    parts.append("<polyline points='" + " ".join(f"{x},{y}" for x, y in sel) + "' fill='none' stroke='#1F4D36' stroke-width='2' stroke-dasharray='8 5'/>")
    for x, y in ((230, 300), (500, 330)):
        parts.append(f"<rect x='{x-8}' y='{y-8}' width='16' height='16' fill='#23272A'/>")
    for x, y in ((60, 280), (370, 90), (330, 280), (200, 560), (560, 560)):
        parts.append(f"<circle cx='{x}' cy='{y}' r='9' fill='none' stroke='#1F4D36' stroke-width='2'/>")
    for x, y in sel:
        parts.append(f"<circle cx='{x}' cy='{y}' r='14' fill='#A6CE39' stroke='#1F4D36' stroke-width='3'><animate attributeName='r' values='13;17;13' dur='2.4s' repeatCount='indefinite'/></circle>")
    return "<svg viewBox='0 0 600 600' width='520' height='520' xmlns='http://www.w3.org/2000/svg'>" + "".join(parts) + "</svg>"


HERO = """<html><body style="margin:0;background:transparent;font-family:Consolas,monospace;overflow:hidden">
<style>.s{position:absolute;left:50%;top:50%;margin:-260px 0 0 -260px;transform:rotateX(58deg) rotateZ(-38deg);filter:drop-shadow(30px 40px 18px rgba(35,39,42,.25));animation:fl 7s ease-in-out infinite}
@keyframes fl{50%{transform:rotateX(58deg) rotateZ(-38deg) translateZ(14px)}}
.l{position:absolute;background:#FBF8EF;border:1px solid #23272A;padding:8px 11px;font-size:11px;letter-spacing:.8px;color:#23272A;line-height:1.5}
.l b{color:#1F4D36;display:block;border-bottom:1px solid #CFCABB;margin-bottom:3px}.l.o{border-left:4px solid #D9822B}.l.g{border-left:4px solid #A6CE39}
.t{position:absolute;font-size:10px;letter-spacing:2px;color:#1F4D36;border:1px solid #1F4D36;padding:1px 5px;background:#F6F2E7}
.ln{position:absolute;height:1px;background:#23272A;transform-origin:left}</style>
<div style="perspective:1500px;position:relative;height:600px;width:100%"><div class="s">SVG</div>
<div class="ln" style="left:150px;top:100px;width:110px;transform:rotate(35deg)"></div>
<div class="l o" style="left:20px;top:50px"><b>DEMAND ZONE 07</b>184 EVs / day<br>+21% projected growth</div>
<div class="ln" style="right:150px;top:262px;width:90px;transform:rotate(-150deg)"></div>
<div class="l" style="right:10px;top:250px"><b>CANDIDATE SITE</b>Grid capacity: 240 kW<br>Installation: &#8377;8.2L</div>
<div class="ln" style="left:230px;top:500px;width:100px;transform:rotate(-30deg)"></div>
<div class="l g" style="left:10px;top:490px"><b>NETWORK SOLUTION</b>6 Stations<br>91% Coverage<br>&#8377;42.5L Investment</div>
<span class="t" style="left:46%;top:14px">A* SEARCH</span><span class="t" style="right:70px;top:120px">CSP</span>
<span class="t" style="left:40%;bottom:30px">HEURISTIC</span><span class="t" style="left:18px;top:220px">BACKTRACKING</span>
<span class="t" style="right:20px;bottom:90px">LOCAL SEARCH</span></div></body></html>""".replace("SVG", city_svg())


# ==============================================================================
# LANDING PAGE RENDERING
# ==============================================================================
def render():
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown(
            f"<div class='hero-container'>"
            f"<h1 class='hero-title-clean'>{HERO_TITLE}</h1>"
            f"<p class='hero-desc-clean'>{HERO_DESCRIPTION}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([1.15, 1.15, 0.7])
        run = b1.button(BUTTON_RUN_LABEL, type="primary", use_container_width=True)
        explore = b2.button(BUTTON_EXPLORE_LABEL, use_container_width=True)
    with right:
        components.html(HERO, height=600)
    if run:
        params = default_params()
        for key in ("allocation_total", "allocation_budget", "allocation_stations", "allocation_distance",
                "allocation_capacity", "allocation_coverage", "allocation_grid"):
            st.session_state.pop(key, None)
        st.session_state["_allocation_params"] = params
        get_result(params)
        st.session_state.page = "Results"
        st.session_state.view = "app"
        st.rerun()
    if explore:
        st.session_state.page = "Overview"
        st.session_state.view = "app"
        st.rerun()
