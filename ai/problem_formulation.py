"""Problem formulation: initial state, state, actions, goal test, path cost."""
import math
from dataclasses import dataclass

EV_PER_KW = 1.5  # EVs/day that 1 kW of charging capacity can serve


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742.0 * math.asin(math.sqrt(a))


@dataclass
class Params:
    total_demand: float = 1530      # EVs/day across Chennai Metropolitan Area
    budget: float = 50.0            # Rs lakh
    max_stations: int = 6
    max_distance: float = 5.0       # km
    min_capacity: float = 120       # kW per station
    required_coverage: float = 0.85
    grid_limit: float = 1400        # kW total new load

    def validate(self):
        for name in ("total_demand", "budget", "max_stations", "max_distance", "min_capacity", "grid_limit"):
            v = getattr(self, name)
            if not isinstance(v, (int, float)) or v <= 0:
                raise ValueError(f"Invalid input: '{name}' must be a positive number.")
        if not 0 < self.required_coverage <= 1:
            raise ValueError("Invalid input: required coverage must be between 1% and 100%.")


class Problem:
    """EV charging allocation as a search problem.
    State = frozenset of selected candidate indices. Action = add one candidate."""

    def __init__(self, sites, zones, params):
        self.p = params
        self.sites = sites.reset_index(drop=True)
        z = zones.reset_index(drop=True).copy()
        z["demand"] = z["demand_share"] / z["demand_share"].sum() * params.total_demand
        self.zones = z
        self.zdem = z["demand"].tolist()
        self.total = sum(self.zdem)
        self.dist = [[haversine(s.latitude, s.longitude, q.latitude, q.longitude) for q in z.itertuples()]
                     for s in self.sites.itertuples()]
        self.cost = self.sites["installation_cost"].tolist()
        self.kw = self.sites["station_capacity"].tolist()
        self.cand = list(range(len(self.sites)))   # reduced later by constraint propagation
        self._cache = {}

    def initial_state(self):
        return frozenset()

    def actions(self, state):
        return [i for i in self.cand if i not in state]

    def result(self, state, action):
        return state | {action}

    def step_cost(self, state, action):
        return self.cost[action] / self.p.budget

    def assign(self, state):
        """Nearest selected station for each zone (None if none within max distance)."""
        out = []
        for j in range(len(self.zdem)):
            best = min(state, key=lambda i: self.dist[i][j], default=None)
            ok = best is not None and self.dist[best][j] <= self.p.max_distance
            out.append(best if ok else None)
        return out

    def metrics(self, state):
        if state in self._cache:
            return self._cache[state]
        asg = self.assign(state)
        cov = sum(d for d, a in zip(self.zdem, asg) if a is not None)
        avg = (sum(d * self.dist[a][j] for j, (d, a) in enumerate(zip(self.zdem, asg)) if a is not None) / cov
               if cov else self.p.max_distance)
        kw = sum(self.kw[i] for i in state)
        cap = kw * EV_PER_KW
        served = min(cov, cap)
        m = dict(n=len(state), cost=sum(self.cost[i] for i in state), kw=kw, coverage=cov / self.total,
                 covered_demand=cov, avg_distance=avg, capacity_ev=cap, served=served,
                 unserved=(self.total - served) / self.total, cap_util=served / cap if cap else 0.0,
                 grid_util=kw / self.p.grid_limit)
        self._cache[state] = m
        return m
