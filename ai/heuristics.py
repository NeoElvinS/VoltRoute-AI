"""Heuristic function: H = w1*distance + w2*cost + w3*unserved + w4*grid (normalised ~0..1)."""
from dataclasses import dataclass


@dataclass
class Weights:
    distance: float = 0.2   # w1
    cost: float = 0.3       # w2
    unserved: float = 0.4   # w3
    grid: float = 0.1       # w4


def components(problem, state):
    m = problem.metrics(state)
    return dict(distance=m["avg_distance"] / problem.p.max_distance if state else 1.0,
                cost=m["cost"] / problem.p.budget, unserved=m["unserved"], grid=m["grid_util"])


def g_cost(problem, state, w):
    """g(n): cost already paid (money + grid load)."""
    c = components(problem, state)
    return w.cost * c["cost"] + w.grid * c["grid"]


def h_estimate(problem, state, w):
    """h(n): estimated remaining cost (distance penalty + demand still unserved)."""
    c = components(problem, state)
    return w.distance * c["distance"] + w.unserved * c["unserved"]
