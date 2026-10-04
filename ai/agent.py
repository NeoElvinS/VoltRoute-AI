"""Intelligent agent: observe -> formulate -> constrain -> search -> improve -> recommend."""
import pandas as pd
from ai.problem_formulation import Problem
from ai.csp import CSP
from ai.constraint_propagation import propagate
from ai.heuristics import Weights
from ai.astar import astar_search
from ai.backtracking import backtracking_search
from ai.local_search import hill_climb
from ai.optimizer import score, score_value

NO_SOLUTION = ("No feasible charging network satisfies the current constraints. "
               "Try increasing the budget or maximum number of stations.")


class ChargingAgent:
    def __init__(self, sites, zones, params, weights=None):
        self.sites, self.zones, self.params = sites, zones, params
        self.weights = weights or Weights()
        self.log = []

    def _fail(self, detail, extra=None):
        r = dict(feasible=False, message=detail, log=self.log)
        r.update(extra or {})
        return r

    @staticmethod
    def _notify(progress_callback, stage, event):
        if progress_callback:
            progress_callback(stage, event)

    def run(self, progress_callback=None):
        self.log = []
        self._notify(progress_callback, "Validating demand inputs", "start")
        try:
            self.params.validate()
        except ValueError as e:
            self._notify(progress_callback, "Validating demand inputs", "failed")
            return self._fail(str(e))
        if self.sites is None or len(self.sites) == 0 or self.zones is None or len(self.zones) == 0:
            self._notify(progress_callback, "Validating demand inputs", "failed")
            return self._fail("The dataset is empty. Please provide candidate locations and demand zones.")

        self._notify(progress_callback, "Validating demand inputs", "complete")
        self._notify(progress_callback, "Formulating allocation problem", "start")
        pr = Problem(self.sites, self.zones, self.params)            # problem formulation
        self._notify(progress_callback, "Formulating allocation problem", "complete")
        self._notify(progress_callback, "Applying CSP constraints", "start")
        csp = CSP(pr)
        self._notify(progress_callback, "Applying CSP constraints", "complete")
        self.log.append(f"Observed {len(pr.cand)} candidate sites and {len(pr.zdem)} demand zones.")
        self._notify(progress_callback, "Propagating constraints", "start")
        prop = propagate(pr, csp)                                    # constraint propagation
        self._notify(progress_callback, "Propagating constraints", "complete")
        self.log.append(f"Propagation: {prop['initial']} -> {prop['remaining']} candidates.")
        base = dict(problem=pr, csp=csp, propagation=prop)
        self._notify(progress_callback, "Checking allocation feasibility", "start")
        if not pr.cand:
            self._notify(progress_callback, "Checking allocation feasibility", "failed")
            self._notify(progress_callback, "Allocation could not be completed", "failed")
            return self._fail(NO_SOLUTION + " (No candidate survived constraint propagation.)", base)
        ub = pr.metrics(frozenset(pr.cand))["coverage"]
        if ub < self.params.required_coverage:
            self._notify(progress_callback, "Checking allocation feasibility", "failed")
            self._notify(progress_callback, "Allocation could not be completed", "failed")
            return self._fail(f"{NO_SOLUTION} (Even all feasible sites give only {ub:.0%} coverage; "
                              f"required {self.params.required_coverage:.0%}.)", base)
        self._notify(progress_callback, "Checking allocation feasibility", "complete")
        self._notify(progress_callback, "Running heuristic search (A*)", "start")
        astar = astar_search(csp, self.weights)                      # heuristic search
        self._notify(progress_callback, "Running heuristic search (A*)", "complete")
        self._notify(progress_callback, "Evaluating alternatives with backtracking", "start")
        bt = backtracking_search(csp, lambda s: score_value(pr, s))  # CSP backtracking
        self._notify(progress_callback, "Evaluating alternatives with backtracking", "complete")
        cands = [x["state"] for x in (astar, bt) if x["state"] is not None]
        if not cands:
            self._notify(progress_callback, "Allocation could not be completed", "failed")
            return self._fail(NO_SOLUTION, dict(base, astar=astar["stats"], backtracking=bt["stats"]))
        start = max(cands, key=lambda s: score_value(pr, s))
        self._notify(progress_callback, "Running local search", "start")
        ls = hill_climb(csp, start)                                  # local search
        self._notify(progress_callback, "Running local search", "complete")
        self._notify(progress_callback, "Optimizing final network", "start")
        final = ls["state"]
        assert csp.is_solution(final)                                # hard constraints always hold
        result = dict(feasible=True, message="Optimal network found.", log=self.log, **base,
                      astar=astar["stats"], astar_state=astar["state"], backtracking=bt["stats"], bt_state=bt["state"],
                      local=ls["stats"], start_state=start, state=final, metrics=pr.metrics(final),
                      score=score(pr, final), table=self._table(pr, final), curve=self._curve(pr, final),
                      explanation=self._explain(pr, final, prop, ls["stats"], astar["stats"]))
        self._notify(progress_callback, "Optimizing final network", "complete")
        self._notify(progress_callback, "Allocation complete", "complete")
        return result

    def _table(self, pr, state):
        asg = pr.assign(state)
        rows = []
        for i in sorted(state):
            zs = [j for j, a in enumerate(asg) if a == i]
            dem = sum(pr.zdem[j] for j in zs)
            avg = sum(pr.zdem[j] * pr.dist[i][j] for j in zs) / dem if dem else 0
            names = ", ".join(pr.zones.loc[j, "zone_name"] for j in zs) or "-"
            s = pr.sites.loc[i]
            head = int(s["grid_capacity"] - pr.kw[i])
            reason = (f"Serves {len(zs)} zone(s) [{names}] = {dem:.0f} EVs/day ({dem / pr.total:.0%} of demand), "
                      f"avg {avg:.1f} km; Rs {pr.cost[i]:.1f}L = Rs {pr.cost[i] * 1e5 / max(dem, 1):.0f} per daily EV; "
                      f"grid headroom {head} kW.")
            rows.append({"Location": s["location_name"], "EV Demand": int(round(dem)),
                         "Installation Cost (Rs L)": pr.cost[i], "Capacity (kW)": pr.kw[i],
                         "Grid Capacity (kW)": int(s["grid_capacity"]), "Distance (km)": round(avg, 1),
                         "Reason Selected": reason})
        return pd.DataFrame(rows)

    def _curve(self, pr, state):
        left, chosen, curve = set(state), frozenset(), [0.0]
        while left:
            nxt = max(left, key=lambda i: pr.metrics(chosen | {i})["coverage"])
            chosen |= {nxt}
            left.discard(nxt)
            curve.append(pr.metrics(chosen)["coverage"])
        return curve

    def _explain(self, pr, state, prop, ls, ast):
        m, p = pr.metrics(state), pr.p
        names = ", ".join(pr.sites.loc[sorted(state), "location_name"])
        return [
            f"Constraint propagation removed {prop['pruned_count']} of {prop['initial']} candidates "
            f"(land, cost, grid, distance, dominance), so search ran on {prop['remaining']} sites.",
            f"A* (f = g + h) explored {ast['explored']} states and pruned {ast['pruned']}; the A* and backtracking "
            f"solutions were compared and the better one was kept.",
            f"Hill climbing improved the score by {ls['improvement']:.1f}% in {ls['iterations']} iteration(s), "
            f"giving {len(state)} stations: {names}.",
            f"Coverage is {m['coverage']:.0%} (required {p.required_coverage:.0%}) with average distance "
            f"{m['avg_distance']:.1f} km (limit {p.max_distance:g} km).",
            f"Cost is Rs {m['cost']:.1f}L of the Rs {p.budget:g}L budget ({m['cost'] / p.budget:.0%}); "
            f"grid load {m['kw']:.0f} of {p.grid_limit:g} kW ({m['grid_util']:.0%}).",
            f"{len(state)} of max {p.max_stations} stations were used - extra stations lower the score "
            f"(cost, grid and count penalties) without enough coverage gain.",
        ]
