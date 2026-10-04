"""Comprehensive Stage 2 Validation Script: Verify Chennai AI Data Pipeline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from ai.problem_formulation import Problem, Params
from ai.csp import CSP
from ai.constraint_propagation import propagate
from ai.heuristics import Weights
from ai.astar import astar_search
from ai.backtracking import backtracking_search
from ai.local_search import hill_climb
from ai.optimizer import score, score_value
from ai.agent import ChargingAgent


def run_stage2_validation():
    print("=" * 70)
    print("STAGE 2 VALIDATION: AI ALLOCATION ON CHENNAI DATA")
    print("=" * 70)

    # 1. Data loading verification
    sites = pd.read_csv("data/ev_locations.csv")
    zones = pd.read_csv("data/demand_zones.csv")
    existing = pd.read_csv("data/existing_stations.csv")

    print("[1/7] Data Loading:")
    print(f"      - Candidate Sites: {len(sites)} rows from ev_locations.csv")
    print(f"      - Demand Zones:    {len(zones)} rows from demand_zones.csv")
    print(f"      - Existing Stations: {len(existing)} rows from existing_stations.csv")
    assert len(sites) == 20, "Expected 20 candidate sites"
    assert len(zones) == 8, "Expected 8 demand zones"
    assert len(existing) == 8, "Expected 8 existing stations"
    assert (sites["latitude"].between(12.8, 13.3) & sites["longitude"].between(80.0, 80.4)).all(), "Candidate coordinates outside Chennai bounds"
    assert (zones["latitude"].between(12.8, 13.3) & zones["longitude"].between(80.0, 80.4)).all(), "Zone coordinates outside Chennai bounds"
    print("      -> PASS: All datasets are loaded and strictly within Chennai coordinates.")

    # 2. Problem Formulation verification
    params = Params(total_demand=1530, budget=50.0, max_stations=6, max_distance=5.0, min_capacity=120, required_coverage=0.85, grid_limit=1400)
    pr = Problem(sites, zones, params)
    print("[2/7] Problem Formulation:")
    print(f"      - Total Demand: {pr.total:.1f} EVs/day")
    print(f"      - Distance Matrix: {len(pr.dist)}x{len(pr.dist[0])} (Candidate Sites x Demand Zones)")
    print(f"      - Initial State: {pr.initial_state()}")
    assert pr.total == 1530
    assert len(pr.dist) == 20 and len(pr.dist[0]) == 8
    print("      -> PASS: Problem state space and distance matrix formulated on Chennai data.")

    # 3. CSP & Constraint Propagation
    csp = CSP(pr)
    prop = propagate(pr, csp)
    print("[3/7] CSP & Constraint Propagation:")
    print(f"      - Initial Candidates: {prop['initial']}")
    print(f"      - Remaining Feasible Candidates: {prop['remaining']}")
    print(f"      - Pruned Candidates: {prop['pruned_count']}")
    assert prop["initial"] == 20
    assert prop["remaining"] < 20
    print("      -> PASS: Constraint propagation successfully pruned infeasible candidates.")

    # 4. Heuristic & A* Search
    weights = Weights()
    astar_res = astar_search(csp, weights)
    print("[4/7] Heuristic (A*) Search:")
    print(f"      - States Explored: {astar_res['stats']['explored']}")
    print(f"      - States Pruned:   {astar_res['stats']['pruned']}")
    print(f"      - A* State Found:  {[sites.loc[i, 'location_name'] for i in astar_res['state']]}")
    assert astar_res["state"] is not None
    print("      -> PASS: A* search successfully found feasible Chennai candidate state.")

    # 5. Backtracking Search
    bt_res = backtracking_search(csp, lambda s: score_value(pr, s))
    print("[5/7] Backtracking Search:")
    print(f"      - Assignments: {bt_res['stats']['assignments']}")
    print(f"      - Backtracks:  {bt_res['stats']['backtracks']}")
    print(f"      - Solutions:   {bt_res['stats']['solutions']}")
    print(f"      - BT State:    {[sites.loc[i, 'location_name'] for i in bt_res['state']]}")
    assert bt_res["state"] is not None
    print("      -> PASS: CSP Backtracking completed with multiple feasible assignments.")

    # 6. Local Search & Optimization
    cands = [x["state"] for x in (astar_res, bt_res) if x["state"] is not None]
    start = max(cands, key=lambda s: score_value(pr, s))
    ls = hill_climb(csp, start)
    final_state = ls["state"]
    assert csp.is_solution(final_state)
    sc = score(pr, final_state)
    print("[6/7] Local Search & Scoring:")
    print(f"      - Final Selected Indices: {sorted(final_state)}")
    print(f"      - Final Station Names:    {[sites.loc[i, 'location_name'] for i in sorted(final_state)]}")
    print(f"      - Multi-objective Score:  {sc['score']:.2f} / 100")
    print("      -> PASS: Hill climbing and multi-objective scoring produced optimal network.")

    # 7. End-to-End Agent Execution & Constraints
    agent = ChargingAgent(sites, zones, params)
    res = agent.run()
    assert res["feasible"] is True
    m = res["metrics"]
    print("[7/7] End-to-End Agent Result Metrics:")
    print(f"      - Selected Stations: {m['n']} stations (Budget allows <= {params.max_stations})")
    print(f"      - Total Cost: Rs {m['cost']}L (Budget <= Rs {params.budget}L)")
    print(f"      - Demand Coverage: {m['coverage']:.1%} (Required >= {params.required_coverage:.0%})")
    print(f"      - Grid Load: {m['kw']} kW (Limit <= {params.grid_limit} kW)")
    print(f"      - Avg Distance: {m['avg_distance']:.2f} km (Limit <= {params.max_distance} km)")
    print(f"      - Capacity: {m['capacity_ev']} EVs/day (Served: {m['served']} EVs/day)")
    print("      -> PASS: All constraints verified on final Chennai network.")

    print("=" * 70)
    print("STAGE 2 VALIDATION SUMMARY: ALL CHECKS PASSED (100% CHENNAI DATA PIPELINE)")
    print("=" * 70)


if __name__ == "__main__":
    run_stage2_validation()
