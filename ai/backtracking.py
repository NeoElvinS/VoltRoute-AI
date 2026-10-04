"""Backtracking search for the CSP (assign each site 1=select / 0=skip, undo on violation)."""
import time


def backtracking_search(csp, score_fn, node_limit=30000):
    pr = csp.problem
    order = sorted(pr.cand, key=lambda i: -pr.metrics(frozenset([i]))["covered_demand"])
    st = dict(assignments=0, backtracks=0, solutions=0)
    best = {"state": None, "score": -1e9}
    t0 = time.time()

    def solve(k, chosen):
        if st["assignments"] >= node_limit:
            return
        if csp.is_solution(chosen):                    # goal reached: record it
            st["solutions"] += 1
            sc = score_fn(chosen)
            if sc > best["score"]:
                best.update(state=chosen, score=sc)
            return
        if k == len(order):
            st["backtracks"] += 1
            return
        # forward check: even selecting all remaining sites cannot reach required coverage
        if pr.metrics(chosen | frozenset(order[k:]))["coverage"] < pr.p.required_coverage:
            st["backtracks"] += 1
            return
        v = order[k]
        for val in csp.domains[v]:
            st["assignments"] += 1
            if val == 1:
                nxt = chosen | {v}
                if csp.violations(nxt):                # partial assignment violates -> BACKTRACK
                    st["backtracks"] += 1
                    continue
                solve(k + 1, nxt)
            else:
                solve(k + 1, chosen)

    solve(0, frozenset())
    st.update(time=time.time() - t0, found=best["state"] is not None, limit_hit=st["assignments"] >= node_limit)
    return dict(state=best["state"], stats=st)
