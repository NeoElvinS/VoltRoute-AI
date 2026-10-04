"""Final objective: normalised reward/penalty score (0-100, higher is better)."""

W = dict(coverage=0.25, capacity=0.30, cost=0.15, distance=0.10, grid=0.10, stations=0.10)


def score(problem, state):
    m, p = problem.metrics(state), problem.p
    parts = dict(coverage=m["coverage"],                      # reward: demand within range
                 capacity=1 - m["unserved"],                  # reward: demand actually servable by kW installed
                 cost=1 - min(m["cost"] / p.budget, 1),       # penalty: money spent
                 distance=1 - min(m["avg_distance"] / p.max_distance, 1),
                 grid=1 - min(m["grid_util"], 1),             # penalty: grid overload
                 stations=1 - m["n"] / p.max_stations)        # penalty: unnecessary stations
    return dict(score=100 * sum(W[k] * parts[k] for k in W), parts=parts)


def score_value(problem, state):
    return score(problem, state)["score"]
