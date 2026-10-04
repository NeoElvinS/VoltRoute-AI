"""Plotly charts in the Living Energy Map palette."""
import plotly.graph_objects as go

GREEN, LIME, ORANGE, STONE, INK = "#1F4D36", "#A6CE39", "#D9822B", "#B5B1A4", "#23272A"


def _style(fig, title, h=320):
    fig.update_layout(title=dict(text=title, font=dict(family="Georgia", size=16, color=GREEN)), height=h,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FBF8EF", font=dict(family="Consolas", color=INK, size=11),
                      margin=dict(l=10, r=10, t=45, b=10), showlegend=False)
    fig.update_xaxes(gridcolor="#E4DFD0")
    fig.update_yaxes(gridcolor="#E4DFD0")
    return fig


def demand_chart(pr):
    z = pr.zones
    return _style(go.Figure(go.Bar(x=z["zone_name"], y=z["demand"].round(0), marker_color=ORANGE)), "EV demand by zone (EVs/day)")


def funnel_chart(res):
    p = res["propagation"]
    n = len(res["state"]) if res.get("feasible") else 0
    fig = go.Figure(go.Bar(x=["Candidates", "After propagation", "Selected"], y=[p["initial"], p["remaining"], n],
                           marker_color=[STONE, GREEN, LIME], text=[p["initial"], p["remaining"], n], textposition="outside"))
    return _style(fig, "Candidate vs selected sites")


def cost_chart(res):
    t, pr = res["table"], res["problem"]
    fig = go.Figure(go.Bar(x=t["Location"], y=t["Installation Cost (Rs L)"], marker_color=GREEN, name="Selected"))
    avg = sum(pr.cost) / len(pr.cost)
    fig.add_hline(y=avg, line_dash="dash", line_color=ORANGE, annotation_text=f"avg candidate Rs {avg:.1f}L")
    return _style(fig, "Installation cost: selected vs average candidate (Rs lakh)")


def coverage_chart(res):
    c = res["curve"]
    fig = go.Figure(go.Scatter(x=list(range(len(c))), y=[v * 100 for v in c], mode="lines+markers",
                               line=dict(color=GREEN), marker=dict(color=LIME, size=9, line=dict(color=GREEN, width=1))))
    fig.add_hline(y=res["problem"].p.required_coverage * 100, line_dash="dash", line_color=ORANGE, annotation_text="required")
    fig.update_xaxes(title="stations added")
    return _style(fig, "Coverage improvement (%)")


def perf_chart(res):
    names = ["A*", "Backtracking", "Local search"]
    t = [res["astar"]["time"] * 1000, res["backtracking"]["time"] * 1000, res["local"]["time"] * 1000]
    fig = go.Figure(go.Bar(x=names, y=t, marker_color=[GREEN, ORANGE, LIME], text=[f"{v:.1f} ms" for v in t], textposition="outside"))
    return _style(fig, "Algorithm performance (execution time)")


def fallback_map(pr, existing, state):
    """Plain scatter 'map' used if Folium cannot render."""
    fig = go.Figure()
    z = pr.zones
    fig.add_trace(go.Scatter(x=z.longitude, y=z.latitude, mode="markers", marker=dict(size=z.demand / 6, color=ORANGE, opacity=.4), name="Demand zones"))
    s = pr.sites
    fig.add_trace(go.Scatter(x=s.longitude, y=s.latitude, mode="markers", marker=dict(color=STONE, size=8), text=s.location_name, name="Candidates"))
    if len(existing):
        fig.add_trace(go.Scatter(x=existing.longitude, y=existing.latitude, mode="markers", marker=dict(color=INK, symbol="square", size=9), name="Existing"))
    if state:
        r = s.loc[sorted(state)]
        fig.add_trace(go.Scatter(x=r.longitude, y=r.latitude, mode="markers", marker=dict(color=GREEN, size=15, line=dict(color=LIME, width=3)), text=r.location_name, name="Recommended"))
    _style(fig, "Network map (offline fallback)", 520)
    fig.update_layout(showlegend=True)
    return fig
