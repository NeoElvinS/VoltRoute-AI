"""Run from the project folder: python tests/test_pipeline.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from ai.agent import ChargingAgent
from ai.problem_formulation import Params

s, z = pd.read_csv("data/ev_locations.csv"), pd.read_csv("data/demand_zones.csv")
r = ChargingAgent(s, z, Params()).run()
print("default:", r["feasible"], r.get("message"))
if r["feasible"]:
    print(r["metrics"]); print(r["score"]["score"], r["propagation"]["initial"], r["propagation"]["remaining"])
    print(r["astar"]["explored"], round(r["astar"]["time"], 2), r["backtracking"], r["local"])
    print(r["table"][["Location", "EV Demand"]])
bad = ChargingAgent(s, z, Params(budget=5)).run()
assert not bad["feasible"]; print("impossible:", bad["message"])
assert not ChargingAgent(s.iloc[0:0], z, Params()).run()["feasible"]
assert not ChargingAgent(s, z, Params(budget=-1)).run()["feasible"]
print("OK")
