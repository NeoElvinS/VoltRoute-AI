"""Main application pages."""
import pandas as pd
import streamlit as st
from ai.agent import ChargingAgent
from ai.problem_formulation import Params, Problem
from ai.heuristics import Weights
from ai.optimizer import W as SCORE_W
from ui.components import header, cards, note, mono
from visualization import charts
from visualization.maps import build_map

PAGES = ["Overview", "Run Allocation", "AI Analysis", "Results"]
ALLOCATION_STAGES = [
    "Validating demand inputs",
    "Formulating allocation problem",
    "Applying CSP constraints",
    "Propagating constraints",
    "Checking allocation feasibility",
    "Running heuristic search (A*)",
    "Evaluating alternatives with backtracking",
    "Running local search",
    "Optimizing final network",
]
AI_PIPELINE = [
    "Problem Formulation",
    "CSP",
    "Constraint Propagation",
    "Heuristic Function",
    "A* Search",
    "Backtracking",
    "Local Search",
    "Optimization",
]
STAT_NOT_EXPOSED = "Statistic not currently exposed by the algorithm."


def default_params():
    return Params()


def get_result(params, sites=None, zones=None, progress_callback=None):
    """Run the agent (cached in session until inputs change)."""
    if sites is None:
        sites, zones = pd.read_csv("data/ev_locations.csv"), pd.read_csv("data/demand_zones.csv")
    key = tuple(vars(params).values())
    if st.session_state.get("_key") != key:
        try:
            st.session_state["_res"] = ChargingAgent(sites, zones, params).run(progress_callback)
        except Exception:   # never show a raw traceback
            if progress_callback:
                progress_callback("Allocation could not be completed", "failed")
            st.session_state["_res"] = dict(
                feasible=False,
                message="Allocation could not be completed. Check the selected constraints and try again.",
                log=[],
            )
        st.session_state["_key"] = key
    return st.session_state["_res"]


def sidebar():
    st.sidebar.markdown("<div class='brand'><b>V</b>VOLTROUTE AI</div>", unsafe_allow_html=True)
    if st.sidebar.button("← Landing page", width="stretch"):
        st.session_state.view = "landing"
        st.rerun()


def allocation_form(params):
    st.markdown("### Allocation Controls")
    total = st.number_input("Total EV demand (EVs/day)", 200, 10000, int(params.total_demand), 100, key="allocation_total")
    budget = st.number_input("Budget (₹ lakh)", 1.0, 500.0, params.budget, 5.0, key="allocation_budget")
    nmax = st.slider("Maximum number of stations", 1, 12, params.max_stations, key="allocation_stations")
    dist = st.slider("Maximum acceptable distance (km)", 1.0, 15.0, params.max_distance, 0.5, key="allocation_distance")
    grid = st.number_input("Grid capacity (kW)", 100, 5000, int(params.grid_limit), 100, key="allocation_grid")
    cap = st.slider("Minimum charging capacity (kW)", 60, 300, int(params.min_capacity), 10, key="allocation_capacity")
    cov = st.slider("Required demand coverage (%)", 50, 100, int(params.required_coverage * 100), key="allocation_coverage")
    submitted = st.button("RUN AI ALLOCATION", type="primary", width="stretch")
    return Params(total, budget, nmax, dist, cap, cov / 100, grid), submitted


def show_map(pr, existing, state, result=None):
    try:
        from streamlit_folium import st_folium
        st_folium(build_map(pr, existing, state, result), height=600, use_container_width=True, returned_objects=[])
    except Exception:
        st.info("Interactive map unavailable - showing offline fallback.")
        st.plotly_chart(charts.fallback_map(pr, existing, state), width="stretch")


def run_allocation_with_progress(params, sites, zones):
    cached_result = st.session_state.get("_res")
    result_key = st.session_state.get("_key")
    current_key = tuple(vars(params).values())
    cached = cached_result is not None and result_key == current_key

    with st.status("Starting AI allocation", expanded=True) as run_status:
        if cached:
            run_status.write("Reusing the saved allocation for unchanged inputs; AI calculations were not repeated.")
            result = get_result(params, sites, zones)
        else:
            progress_bar = st.progress(0, text="Waiting for the first pipeline stage")
            completed_stages = set()

            def show_stage(stage, event):
                if event == "start":
                    run_status.update(label=stage, state="running", expanded=True)
                elif event == "complete":
                    run_status.write(f"✓ {stage}")
                    if stage in ALLOCATION_STAGES:
                        completed_stages.add(stage)
                        progress_bar.progress(
                            len(completed_stages) / len(ALLOCATION_STAGES),
                            text=f"{len(completed_stages)} of {len(ALLOCATION_STAGES)} stages complete",
                        )
                elif event == "failed":
                    run_status.write(stage)
                    run_status.update(label="Allocation could not be completed", state="error", expanded=True)

            result = get_result(params, sites, zones, show_stage)

    if result.get("feasible"):
        run_status.update(label="AI ALLOCATION COMPLETE", state="complete", expanded=True)
    else:
        run_status.update(label="Allocation could not be completed", state="error", expanded=True)
    return result


def render(sites, zones, existing):
    sidebar()
    st.markdown("<div class='brand'><b>V</b>VOLTROUTE AI &nbsp;·&nbsp; CHENNAI METROPOLITAN REGION</div>", unsafe_allow_html=True)
    page = st.radio("nav", PAGES, horizontal=True, key="page", label_visibility="collapsed")
    params = st.session_state.get("_allocation_params", default_params())
    res = st.session_state.get("_res")
    if page in ("Overview", "Run Allocation"):
        overview(sites, zones, existing, params, page)
        return
    if page == "Results" and (res is None or not res.get("feasible")):
        results_empty(params, sites, zones, existing, res)
        return
    if res is None:
        st.info("Configure the allocation and run the AI agent to generate a recommended charging network.")
        return
    if st.session_state.get("_key") != tuple(vars(params).values()):
        st.info("Showing the last completed allocation. Current inputs have changed; run the AI agent to refresh this analysis.")
    if not res.get("feasible"):
        st.error(res.get("message", "No feasible charging network was found."))
        return
    try:
        pr = res["problem"]
        if page == "AI Analysis":
            ai_analysis(res, pr, existing)
        else:
            results(res, pr, existing)
    except Exception as e:
        st.warning(f"This page could not be displayed ({e}). Try changing the configuration.")


def overview(sites, zones, existing, params, page):
    header(page, "EV Charging Station Allocation Control Center")
    left, right = st.columns([0.9, 2.1], gap="large")
    with left:
        current_params, submitted = allocation_form(params)
        st.session_state["_allocation_params"] = current_params
    with right:
        st.markdown("#### Interactive Chennai map")
        result = st.session_state.get("_res")
        result_key = st.session_state.get("_key")
        current_key = tuple(vars(current_params).values())
        if submitted:
            st.session_state["_allocation_params"] = current_params
            result = run_allocation_with_progress(current_params, sites, zones)
            result_key = st.session_state.get("_key")
        has_current_result = result is not None and result_key == current_key
        if has_current_result and result.get("feasible"):
            st.caption("INPUTS  →  AI ALLOCATION  →  RECOMMENDATION")
            show_map(result["problem"], existing, result.get("state", frozenset()), result)
        elif result is not None and not result.get("feasible") and has_current_result:
            st.error(result.get("message", "No feasible charging network was found."))
            preview = Problem(sites, zones, current_params)
            show_map(preview, existing, frozenset())
        else:
            if result is None:
                st.info("Configure the allocation and run the AI agent to generate a recommended charging network.")
            else:
                st.info("Allocation inputs changed. Run the AI agent to refresh the current recommendation.")
            preview = Problem(sites, zones, current_params)
            show_map(preview, existing, frozenset())
    if has_current_result and result.get("feasible"):
        metrics = result["metrics"]
        st.markdown("### Live allocation metrics")
        cards([("Demand coverage", f"{metrics['coverage']:.1%}", "l2"),
               ("Average distance", f"{metrics['avg_distance']:.2f} km"),
               ("Installation cost", f"₹{metrics['cost']:.1f}L"),
               ("Recommended stations", metrics["n"])])
        cards([("Capacity utilization", f"{metrics['cap_util']:.1%}"),
               ("Grid utilization", f"{metrics['grid_util']:.1%}"),
               ("AI score", f"{result['score']['score']:.2f}", "o")])
    elif has_current_result:
        st.caption("No allocation metrics are available for an infeasible run.")


def ai_analysis(res, pr, existing):
    header("AI Analysis", "Algorithm explorer")
    selected = st.session_state.get(
        "_ai_analysis_choice",
        st.session_state.get("_selected_ai_analysis", AI_PIPELINE[0]),
    )
    pipeline_column, detail_column = st.columns([0.9, 2.1], gap="large")
    with pipeline_column:
        st.markdown("### Current pipeline")
        for index, stage in enumerate(AI_PIPELINE):
            background = "#1F4D36" if stage == selected else "#FBF8EF"
            foreground = "#F6F2E7" if stage == selected else "#23272A"
            border = "#1F4D36" if stage == selected else "#DCD7C9"
            st.markdown(
                f"<div style='padding:7px 10px;border:1px solid {border};background:{background};"
                f"color:{foreground};font-size:13px'>{index + 1:02d} &nbsp; {stage}</div>",
                unsafe_allow_html=True,
            )
            if index < len(AI_PIPELINE) - 1:
                st.markdown("<div style='text-align:center;color:#7A8079;line-height:1.1'>↓</div>", unsafe_allow_html=True)

    with detail_column:
        selected = st.selectbox(
            "Select an algorithm",
            AI_PIPELINE,
            index=AI_PIPELINE.index(selected),
            key="_ai_analysis_choice",
        )
        st.session_state["_selected_ai_analysis"] = selected
        st.markdown(f"### {selected}")
        what, how = _algorithm_explanation(selected, pr, res)
        st.markdown("**WHAT IT DOES**")
        st.write(what)
        st.markdown("**HOW VOLTROUTE USES IT**")
        st.write(how)
        st.markdown("#### Current run")
        _algorithm_metrics(selected, res, pr)


def _algorithm_explanation(stage, pr, res):
    explanations = {
        "Problem Formulation": (
            "Turns the demand, candidate sites, and controls into a searchable allocation problem.",
            f"Builds the current model from {len(pr.sites)} candidate sites and {len(pr.zones)} demand zones.",
        ),
        "CSP": (
            "Represents each candidate as selected or skipped and checks the hard allocation constraints.",
            "Checks budget, station count, grid, capacity, coverage, and distance feasibility.",
        ),
        "Constraint Propagation": (
            "Removes individually infeasible and dominated candidates before search.",
            "Reduced the current candidate set from {initial} to {remaining}.".format(
                initial=res["propagation"]["initial"], remaining=res["propagation"]["remaining"]
            ),
        ),
        "Heuristic Function": (
            "Estimates the remaining search cost from distance, installation cost, unserved demand, and grid load.",
            "Provides the h(n) estimate used by A* to prioritize candidate networks.",
        ),
        "A* Search": (
            "Expands the state with the lowest estimated total cost, f(n) = g(n) + h(n).",
            "Searches feasible station combinations using the current problem and heuristic weights.",
        ),
        "Backtracking": (
            "Explores select/skip assignments and backs out when a partial assignment cannot lead to a solution.",
            "Evaluates CSP assignments and returns valid solutions for comparison with A*.",
        ),
        "Local Search": (
            "Tries add, remove, and replace neighbors, keeping feasible changes that improve the score.",
            "Refines the better feasible starting network found by A* or backtracking.",
        ),
        "Optimization": (
            "Scores the final network using normalized coverage, capacity, cost, distance, grid, and station-count components.",
            "Ranks the final allocation and supplies the score and network metrics shown in Results.",
        ),
    }
    return explanations[stage]


def _algorithm_metrics(stage, res, pr):
    csp = res["csp"]
    propagation = res["propagation"]
    astar = res["astar"]
    backtracking = res["backtracking"]
    local = res["local"]
    metrics = res["metrics"]
    unavailable = []

    if stage == "Problem Formulation":
        cards([("Initial candidate sites", propagation["initial"]),
               ("Demand zones", len(pr.zones)),
               ("Total demand", f"{pr.total:.0f} EVs/day")])
    elif stage == "CSP":
        cards([("Variables", len(csp.variables)),
               ("Domain values", "1 / 0"),
               ("Global constraints", len(csp.constraints)),
               ("Feasible candidates", propagation["remaining"])])
        st.caption("1 = selected, 0 = skipped. Per-site checks: capacity, local grid, and distance.")
    elif stage == "Constraint Propagation":
        cards([("Initial candidates", propagation["initial"]),
               ("Feasible candidates", propagation["remaining"], "l2"),
               ("Pruned candidates", propagation["pruned_count"], "o")])
    elif stage == "Heuristic Function":
        weights = Weights()
        cards([("Distance weight", weights.distance),
               ("Cost weight", weights.cost),
               ("Unserved-demand weight", weights.unserved),
               ("Grid weight", weights.grid)])
        value = astar.get("h")
        if value is None:
            _show_unavailable([("A* heuristic value", value)])
        else:
            cards([("A* heuristic value (h)", f"{value:.3f}")])
    elif stage == "A* Search":
        astar_stats = []
        for label, key, formatter in (
            ("States explored", "explored", str),
            ("States pruned", "pruned", str),
            ("Path cost (g)", "g", lambda value: f"{value:.3f}"),
            ("Heuristic value (h)", "h", lambda value: f"{value:.3f}"),
        ):
            value = astar.get(key)
            if value is None:
                unavailable.append(label)
            else:
                astar_stats.append((label, formatter(value)))
        if astar_stats:
            cards(astar_stats)
        _show_unavailable([(label, None) for label in unavailable])
    elif stage == "Backtracking":
        cards([("Assignments tested", backtracking.get("assignments", STAT_NOT_EXPOSED)),
               ("Backtracks", backtracking.get("backtracks", STAT_NOT_EXPOSED)),
               ("Valid solutions", backtracking.get("solutions", STAT_NOT_EXPOSED))])
        _show_unavailable([("Rejected assignments", None)])
    elif stage == "Local Search":
        cards([("Initial score", f"{local['initial_score']:.2f}"),
               ("Iterations", local["iterations"]),
               ("Final score", f"{local['final_score']:.2f}", "l2"),
               ("Improvement", f"{local['improvement']:.2f}%", "o")])
    else:
        cards([("Initial score", f"{local['initial_score']:.2f}"),
               ("Final score", f"{res['score']['score']:.2f}", "l2"),
               ("Coverage", f"{metrics['coverage']:.1%}")])
        cards([("Installation cost", f"₹{metrics['cost']:.1f}L"),
               ("Average distance", f"{metrics['avg_distance']:.2f} km"),
               ("Grid usage", f"{metrics['grid_util']:.1%}")])


def _show_unavailable(items):
    for label, _ in items:
        st.caption(f"{label}: {STAT_NOT_EXPOSED}")


def demand(res, pr, existing):
    header("EV Demand", "Demand by zone")
    st.plotly_chart(charts.demand_chart(pr), width="stretch")
    z = pr.zones[["zone_id", "zone_name", "latitude", "longitude", "demand"]].copy()
    z["demand"] = z["demand"].round(0).astype(int)
    st.dataframe(z.rename(columns={"demand": "EVs/day"}), hide_index=True, width="stretch")


def candidates(res, pr, existing):
    header("Candidate Sites", "Site screening")
    p = res["propagation"]
    cards([("Initial candidates", p["initial"]), ("After propagation", p["remaining"], "l2"), ("Pruned", p["pruned_count"], "o")])
    st.dataframe(pr.sites.drop(columns=["latitude", "longitude"]), hide_index=True, width="stretch")
    if p["pruned"]:
        st.markdown("**Pruned sites and reasons**")
        st.dataframe(pd.DataFrame(p["pruned"], columns=["Site", "Reason"]), hide_index=True, width="stretch")
    if res["feasible"]:
        st.plotly_chart(charts.funnel_chart(res), width="stretch")


def constraints(res, pr, existing):
    header("Constraints", "Allocation limits")
    p = pr.p
    rows = [("Budget limit", f"total cost ≤ ₹{p.budget:g}L"), ("Maximum stations", f"count ≤ {p.max_stations}"),
            ("Minimum capacity", f"each station ≥ {p.min_capacity:g} kW"), ("Grid capacity", f"site grid ≥ station kW; total ≤ {p.grid_limit:g} kW"),
            ("Maximum distance", f"station must serve a zone within {p.max_distance:g} km"), ("Required coverage", f"covered demand ≥ {p.required_coverage:.0%}")]
    if res["feasible"]:
        viol = res["csp"].violations(res["state"], complete=True)
        for r in rows:
            r += ("✅ satisfied" if not viol else "❌",)
        rows = [r + ("✅ satisfied",) for r in rows]
    st.dataframe(pd.DataFrame(rows, columns=["Constraint", "Rule"] + (["Final network"] if res["feasible"] else [])), hide_index=True, width="stretch")
    note("The final network is checked against every hard constraint.")


def ai_search(res, pr, existing):
    header("Search", "Search performance")
    st.dataframe(pd.DataFrame([
        ("Initial state", "{ }  - no charging stations selected"), ("State", "A set of selected candidate sites, e.g. {A, C}"),
        ("Actions", "Select one more candidate location"), ("Goal state", "Feasible network meeting coverage, budget, grid and station limits"),
        ("Path cost", "g = w2·cost/budget + w4·grid load; remaining h = w1·distance + w3·unserved demand")],
        columns=["Element", "EV allocation problem"]), hide_index=True, width="stretch")
    w = Weights()
    mono(f"H = w1·distance_penalty + w2·installation_cost + w3·demand_unserved + w4·grid_penalty &nbsp; (w1={w.distance}, w2={w.cost}, w3={w.unserved}, w4={w.grid})")
    mono("f(n) = g(n) + h(n)")
    if res["feasible"]:
        a, b = res["astar"], res["backtracking"]
        st.markdown("**A\\* search**")
        cards([("States explored", a["explored"]), ("States pruned", a["pruned"], "o"), ("Final cost g", f"{a['g']:.3f}"),
               ("Heuristic h", f"{a['h']:.3f}"), ("Time", f"{a['time']*1000:.1f} ms")])
        st.markdown("First expanded states (state-space sample): " + " → ".join(
            "{" + ",".join(pr.sites.loc[s, 'location_id']) + f"}} (f={f})" if s else f"{{ }} (f={f})" for s, f in a["trace"][:6]))
        st.markdown("**Backtracking search (CSP)**")
        cards([("Assignments explored", b["assignments"]), ("Backtracks", b["backtracks"], "o"), ("Feasible solutions", b["solutions"], "l2"),
               ("Time", f"{b['time']*1000:.1f} ms")])
        if a["limit_hit"] or b["limit_hit"]:
            note("A search limit was reached to keep runtime short; the best solution found so far is used.")


def optimization(res, pr, existing):
    header("Optimization", "Network score")
    if not res["feasible"]:
        return
    l = res["local"]
    cards([("Initial score", f"{l['initial_score']:.2f}"), ("Final score", f"{l['final_score']:.2f}", "l2"),
           ("Iterations", l["iterations"]), ("Improvement", f"{l['improvement']:.2f}%", "o")])
    st.markdown("**Score = Σ weight × normalised component** (each component scaled 0-1 so none dominates)")
    parts = res["score"]["parts"]
    st.dataframe(pd.DataFrame([(k.title(), SCORE_W[k], round(parts[k], 3), round(100 * SCORE_W[k] * parts[k], 2)) for k in SCORE_W],
                              columns=["Component", "Weight", "Value (0-1)", "Points"]), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    c1.plotly_chart(charts.coverage_chart(res), width="stretch")
    c2.plotly_chart(charts.cost_chart(res), width="stretch")


def algorithms(res, pr, existing):
    header("Algorithms", "Methods used")
    f = res["feasible"]
    p, a, b, l = res["propagation"], res.get("astar"), res.get("backtracking"), res.get("local")
    live = lambda x: x if f else "-"
    rows = [
        ("Intelligent Agent", "Perceive demand data, decide, act", "CSV data + inputs", "Recommended network", "Coordinates the whole pipeline", f"{len(res['log'])} log entries" if f else "-"),
        ("Problem Formulation", "Define states/actions/goal", "Real-world problem", "Search problem", "Makes the problem solvable by search", "Initial state = { }"),
        ("State Space", "All station combinations", "Candidates", "Set of states", "Search moves through it", f"{a['explored']} states visited" if f else "-"),
        ("Heuristic Function", "Estimate remaining cost", "State", "Number H", "Guides A* to promising states", f"h = {a['h']:.3f}" if f else "-"),
        ("Heuristic Search (A*)", "Find a goal state cheaply", "Start state + H", "Feasible network", "Expands best f = g + h first", f"{a['pruned']} pruned" if f else "-"),
        ("CSP", "Formal variables/domains/constraints", "Sites + limits", "Feasibility test", "Checks hard constraints exactly", f"{len(pr.cand)} variables"),
        ("Constraint Propagation", "Remove infeasible sites early", "All candidates", "Smaller candidate set", "Shrinks the search space", f"{p['initial']} → {p['remaining']}"),
        ("Backtracking", "Systematic assignment with undo", "Ordered sites", "Feasible solutions", "Complete search of the CSP", f"{b['backtracks']} backtracks" if f else "-"),
        ("Local Search", "Improve a valid solution", "Best found network", "Better network", "Escapes poor initial choices", f"+{l['improvement']:.2f}%" if f else "-"),
        ("Optimization", "Rank solutions", "Metrics", "Score 0-100", "Balances coverage, cost, distance, grid", f"{res['score']['score']:.1f}" if f else "-")]
    st.dataframe(pd.DataFrame(rows, columns=["Concept", "Purpose", "Input", "Output", "Why used", "This run"]), hide_index=True, width="stretch")
    if f:
        st.plotly_chart(charts.perf_chart(res), width="stretch")


def results_empty(params, sites, zones, existing, result=None):
    header("Results", "OPTIMIZED CHARGING NETWORK")
    if result is not None and not result.get("feasible"):
        st.error(result.get("message", "Allocation could not be completed. Check the selected constraints."))
    if st.button("RUN AI ALLOCATION", type="primary", key="results_empty_run"):
        st.session_state["_allocation_params"] = params
        result = run_allocation_with_progress(params, sites, zones)
        if result.get("feasible"):
            st.rerun()
        else:
            st.info("No allocation has been generated yet.")
            st.error(result.get("message", "Allocation could not be completed. Check the selected constraints."))
    else:
        st.info("No allocation has been generated yet.")


def results(res, pr, existing):
    header("Results", "OPTIMIZED CHARGING NETWORK")
    if not res["feasible"]:
        return

    table = res["table"]
    metrics = res["metrics"]
    station_names = ", ".join(table["Location"].tolist())
    st.markdown("#### Recommended Stations")
    st.write(station_names)
    cards([("Demand coverage", f"{metrics['coverage']:.1%}", "l2"),
           ("Average distance", f"{metrics['avg_distance']:.2f} km"),
           ("Total installation cost", f"₹{metrics['cost']:.1f}L"),
           ("Charging capacity", f"{metrics['kw']:.0f} kW")])
    cards([("Grid utilization", f"{metrics['grid_util']:.1%}"),
           ("AI optimization score", f"{res['score']['score']:.2f} / 100", "o"),
           ("Number of stations", metrics["n"])])

    st.markdown(
        "VoltRoute AI recommends these locations because they provide the best balance between "
        "demand coverage, installation cost, distance, capacity and grid constraints."
    )
    st.caption(
        f"This run selected {metrics['n']} stations, covering {metrics['coverage']:.1%} of demand "
        f"at an average {metrics['avg_distance']:.2f} km, for ₹{metrics['cost']:.1f}L with "
        f"{metrics['kw']:.0f} kW capacity and {metrics['grid_util']:.1%} grid utilization."
    )

    show_map(pr, existing, res.get("state", frozenset()), res)

    st.markdown("### Recommended station details")
    for start in range(0, len(table), 2):
        station_columns = st.columns(2)
        for column, (_, station) in zip(station_columns, table.iloc[start:start + 2].iterrows()):
            with column:
                with st.container(border=True):
                    st.markdown(f"#### {station['Location']}")
                    st.caption("Why selected")
                    st.write(station["Reason Selected"])
                    values = st.columns(3)
                    values[0].metric("Demand served", f"{station['EV Demand']:.0f} EVs/day")
                    values[1].metric("Distance", f"{station['Distance (km)']:.2f} km")
                    values[2].metric("Cost", f"₹{station['Installation Cost (Rs L)']:.1f}L")
                    values = st.columns(3)
                    values[0].metric("Capacity", f"{station['Capacity (kW)']:.0f} kW")
                    grid_limit = station["Grid Capacity (kW)"]
                    capacity = station["Capacity (kW)"]
                    grid_share = capacity / grid_limit if grid_limit else 0.0
                    values[1].metric(
                        "Grid impact",
                        f"{capacity:.0f} / {grid_limit:.0f} kW ({grid_share:.1%})",
                    )
                    values[2].metric("AI score (network)", f"{res['score']['score']:.2f} / 100")

    st.download_button("Download network (CSV)", table.to_csv(index=False), "recommended_network.csv", "text/csv")
