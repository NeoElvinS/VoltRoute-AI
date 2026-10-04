"""A* search over station-combination states: f(n) = g(n) + h(n)."""
import heapq
import time
from ai.heuristics import g_cost, h_estimate, Weights


def astar_search(csp, w=None, max_expansions=20000):
    w = w or Weights()
    pr = csp.problem
    t0 = time.time()
    pos = {c: k for k, c in enumerate(pr.cand)}
    start = pr.initial_state()
    heap = [(g_cost(pr, start, w) + h_estimate(pr, start, w), 0, start)]
    counter = explored = pruned = 0
    trace, found, f_goal = [], None, None
    while heap and explored < max_expansions:
        f, _, s = heapq.heappop(heap)
        explored += 1
        if len(trace) < 8:
            trace.append((sorted(s), round(f, 3)))
        if csp.is_solution(s):
            found, f_goal = s, f
            break
        last = max((pos[i] for i in s), default=-1)
        for a in pr.cand[last + 1:]:          # fixed order -> no duplicate states
            child = pr.result(s, a)
            if csp.violations(child):         # constraint violated -> prune
                pruned += 1
                continue
            counter += 1
            heapq.heappush(heap, (g_cost(pr, child, w) + h_estimate(pr, child, w), counter, child))
    stats = dict(found=found is not None, explored=explored, pruned=pruned, time=time.time() - t0, trace=trace,
                 limit_hit=found is None and explored >= max_expansions)
    if found is not None:
        stats.update(g=g_cost(pr, found, w), h=h_estimate(pr, found, w), f=f_goal)
    return dict(state=found, stats=stats)
