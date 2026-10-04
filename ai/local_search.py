"""Hill-climbing local search: add / remove / replace a station while the score improves."""
import time
from ai.optimizer import score_value


def neighbours(problem, state):
    out = [state | {a} for a in problem.cand if a not in state]
    out += [state - {s} for s in state]
    out += [(state - {s}) | {a} for s in state for a in problem.cand if a not in state]
    return out


def hill_climb(csp, start, max_iter=100):
    pr = csp.problem
    t0 = time.time()
    cur, cur_sc = start, score_value(pr, start)
    first, it = cur_sc, 0
    while it < max_iter:
        best, best_sc = None, cur_sc
        for n in neighbours(pr, cur):
            if csp.is_solution(n):                    # only feasible neighbours
                sc = score_value(pr, n)
                if sc > best_sc + 1e-9:
                    best, best_sc = n, sc
        if best is None:
            break                                     # local optimum
        cur, cur_sc, it = best, best_sc, it + 1
    imp = (cur_sc - first) / first * 100 if first else 0
    return dict(state=cur, stats=dict(initial_score=first, final_score=cur_sc, iterations=it,
                                       improvement=imp, time=time.time() - t0))
