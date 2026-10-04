"""Living Energy Map theme: ivory, charcoal, forest green, lime, muted orange, stone."""
import base64

_TOPO = ("<svg xmlns='http://www.w3.org/2000/svg' width='800' height='800' fill='none' stroke='#1F4D36' "
         "stroke-opacity='.042' stroke-width='0.9'>" + "".join(f"<ellipse cx='{cx}' cy='{cy}' rx='{r*1.35}' ry='{r}'/>"
         for cx, cy in ((110, 130), (710, 690)) for r in range(40, 340, 32)) + "</svg>")
TOPO = "data:image/svg+xml;base64," + base64.b64encode(_TOPO.encode()).decode()

CSS = """<style>
:root {
  --ivory: #F6F2E7;
  --ink: #23272A;
  --forest: #1F4D36;
  --forest-dark: #163827;
  --lime: #A6CE39;
  --orange: #D9822B;
  --stone: #7A8079;
  --line: #DCD7C9;
  --line-subtle: #E8E3D7;
}

.stApp {
  background-color: var(--ivory);
  color: var(--ink);
  background-image: url(TOPO_URI),
    linear-gradient(rgba(31, 77, 54, 0.026) 1px, transparent 1px),
    linear-gradient(90deg, rgba(31, 77, 54, 0.026) 1px, transparent 1px);
  background-size: 800px 800px, 44px 44px, 44px 44px;
}

header[data-testid="stHeader"] {
  background: transparent;
}
#MainMenu, footer {
  visibility: hidden;
}

h1, h2, h3 {
  font-family: Georgia, 'Times New Roman', serif !important;
  color: var(--forest) !important;
  letter-spacing: 0;
  font-weight: normal;
}

h1 { font-size: 2.2rem !important; line-height: 1.12 !important; }
h2 { font-size: 1.65rem !important; line-height: 1.2 !important; margin: .25rem 0 .7rem !important; }
h3 { font-size: 1.2rem !important; line-height: 1.25 !important; margin: .3rem 0 .5rem !important; }
h4 { font-size: 1rem !important; line-height: 1.3 !important; margin: .25rem 0 .5rem !important; }

html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.stMainBlockContainer {
  padding-top: 1.15rem;
  padding-bottom: 1.8rem;
  padding-left: 1.6rem;
  padding-right: 1.6rem;
}

section.main div[data-testid="stVerticalBlock"] {
  gap: .8rem;
}

.stCaption, [data-testid="stCaptionContainer"] {
  color: #626A64;
  line-height: 1.45;
}

.stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
  overflow-wrap: anywhere;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
  background: #EDE8D8;
  border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] .block-container {
  padding-top: 1.25rem;
  padding-left: 1rem;
  padding-right: 1rem;
}

/* General Brand / Tag elements */
.brand {
  font-family: Consolas, 'SF Mono', Monaco, monospace;
  font-weight: 700;
  font-size: 11px;
  color: var(--forest);
  letter-spacing: 1.3px;
}
.brand b {
  background: var(--lime);
  padding: 1px 6px;
  margin-right: 6px;
  color: var(--ink);
  border-radius: 2px;
}

.tag {
  font-family: Consolas, 'SF Mono', Monaco, monospace;
  font-size: 10.5px;
  letter-spacing: 1px;
  color: var(--stone);
  text-transform: uppercase;
  border-top: 1px solid var(--line);
  padding-top: 6px;
  margin-top: 6px;
}

/* Landing Page Clean Hero Styles */
.hero-container {
  padding-top: 48px;
  max-width: 620px;
}

.hero-title-clean {
  font-family: Georgia, 'Times New Roman', 'Newsreader', serif !important;
  font-size: 58px !important;
  font-weight: 400 !important;
  line-height: 1.08 !important;
  color: var(--forest) !important;
  letter-spacing: -0.5px !important;
  margin: 0 0 18px 0 !important;
}

.hero-desc-clean {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
  font-size: 16.5px !important;
  line-height: 1.5 !important;
  color: #424945 !important;
  max-width: 560px !important;
  margin: 0 0 34px 0 !important;
  font-weight: 400 !important;
}

/* Button Refinement */
.stButton > button {
  height: 44px !important;
  min-height: 44px !important;
  font-family: Consolas, 'SF Mono', Monaco, monospace !important;
  font-size: 11.5px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  border-radius: 3px !important;
  border: 1.5px solid var(--forest) !important;
  background: transparent !important;
  color: var(--forest) !important;
  cursor: pointer;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease !important;
  padding: 0 16px !important;
  box-shadow: none !important;
}

.stButton > button[kind="primary"] {
  background: var(--forest) !important;
  color: #F6F2E7 !important;
  border-color: var(--forest) !important;
  font-size: 12px !important;
  min-height: 48px !important;
  box-shadow: 0 2px 5px rgba(31, 77, 54, .14) !important;
}

.stButton > button[kind="primary"]:hover {
  background: var(--forest-dark) !important;
  border-color: var(--forest-dark) !important;
  color: #FFFFFF !important;
}

.stButton > button:not([kind="primary"]):hover {
  background: rgba(31, 77, 54, 0.06) !important;
  border-color: var(--forest-dark) !important;
  color: var(--forest-dark) !important;
}

.stButton > button:focus-visible {
  outline: 3px solid var(--lime) !important;
  outline-offset: 2px !important;
}

/* UI Card & Utility Components */
.card {
  background: #FBF8EF;
  border: 1px solid var(--line);
  border-left: 4px solid var(--forest);
  border-radius: 3px;
  padding: 11px 13px;
  margin-bottom: 7px;
  min-height: 76px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.card .v {
  font-family: Georgia, serif;
  font-size: 23px;
  line-height: 1.2;
  color: var(--ink);
  overflow-wrap: anywhere;
}
.card .l {
  font-family: Consolas, monospace;
  font-size: 10px;
  line-height: 1.35;
  letter-spacing: .6px;
  color: var(--stone);
  text-transform: uppercase;
  overflow-wrap: anywhere;
}
.card.o {
  border-left-color: var(--orange);
}
.card.l2 {
  border-left-color: var(--lime);
}

.note {
  background: #FBF8EF;
  border: 1px dashed var(--stone);
  padding: 10px 14px;
  font-size: 14px;
  margin: 8px 0;
}

[data-testid="stAlert"] {
  border-radius: 3px;
  border-width: 1px;
}

[data-testid="stStatusWidget"] {
  border-radius: 3px;
  border-color: var(--line);
}
.mono {
  font-family: Consolas, monospace;
  font-size: 13px;
  background: #FBF8EF;
  border: 1px solid var(--line);
  padding: 8px 12px;
  display: block;
  margin: 6px 0;
}

.step {
  font-family: Consolas, monospace;
  color: var(--forest);
  padding: 3px 0;
  font-size: 14px;
  letter-spacing: 0.5px;
}
.step.d {
  color: var(--stone);
}

div[role="radiogroup"] {
  gap: 3px;
  border-bottom: 1px solid var(--forest);
  flex-wrap: wrap;
  padding-bottom: 3px;
}
div[role="radiogroup"] label {
  padding: 7px 12px;
  margin: 0;
  border: 1px solid transparent;
  border-bottom: none;
  font-family: Consolas, monospace;
  text-transform: uppercase;
  letter-spacing: .5px;
  cursor: pointer;
  border-radius: 3px 3px 0 0;
}
div[role="radiogroup"] label > div:first-child {
  display: none;
}
div[role="radiogroup"] label:has(input:checked) {
  background: var(--forest);
  color: #F6F2E7;
}
div[role="radiogroup"] label:has(input:checked) p {
  color: #F6F2E7;
}

.leaflet-container {
  background: #EFEADA !important;
}

div[data-testid="stDataFrame"], div[data-testid="stTable"] {
  max-width: 100%;
}

@media (max-width: 1050px) {
  .stMainBlockContainer {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .card .v { font-size: 21px; }
  div[role="radiogroup"] label { padding: 6px 9px; font-size: 11px; }
}

@media (max-width: 700px) {
  .stMainBlockContainer {
    padding-top: .8rem;
    padding-left: .7rem;
    padding-right: .7rem;
  }
  h2 { font-size: 1.4rem !important; }
  h3 { font-size: 1.1rem !important; }
  .card { min-height: 68px; padding: 9px 10px; }
  .card .v { font-size: 19px; }
  .card .l { font-size: 9px; }
  div[role="radiogroup"] { gap: 2px; }
  div[role="radiogroup"] label { padding: 6px 7px; font-size: 10px; }
  .stButton > button { padding: 0 10px !important; font-size: 10px !important; }
}

/* Responsive queries */
@media (max-width: 1200px) {
  .hero-container {
    padding-top: 24px;
  }
  .hero-title-clean {
    font-size: 44px !important;
  }
  .hero-desc-clean {
    font-size: 15.5px !important;
  }
}
@media (max-width: 900px) {
  .hero-container {
    padding-top: 12px;
  }
  .hero-title-clean {
    font-size: 36px !important;
  }
  .hero-desc-clean {
    font-size: 15px !important;
    margin-bottom: 24px !important;
  }
}
</style>""".replace("TOPO_URI", "'" + TOPO + "'")
