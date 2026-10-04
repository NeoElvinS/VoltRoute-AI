"""CSP model: variables = candidate sites, domain = {1 selected, 0 not selected}."""


class CSP:
    def __init__(self, problem):
        self.problem = problem
        self.variables = list(problem.cand)
        self.domains = {v: (1, 0) for v in self.variables}
        p = problem.p
        # (name, test on metrics, also checked on partial assignments?)
        self.constraints = [
            ("Budget limit", lambda m: m["cost"] <= p.budget, True),
            ("Maximum stations", lambda m: m["n"] <= p.max_stations, True),
            ("Grid capacity limit", lambda m: m["kw"] <= p.grid_limit, True),
            ("Required coverage", lambda m: m["coverage"] >= p.required_coverage, False),
        ]

    def site_violations(self, i):
        """Unary constraints on one site."""
        pr, p = self.problem, self.problem.p
        bad = []
        if pr.kw[i] < p.min_capacity:
            bad.append("Minimum station capacity")
        if pr.sites.loc[i, "grid_capacity"] < pr.kw[i]:
            bad.append("Local grid capacity")
        if min(pr.dist[i]) > p.max_distance:
            bad.append("Maximum distance")
        return bad

    def violations(self, state, complete=False):
        """Names of violated constraints (partial check unless complete=True)."""
        m = self.problem.metrics(state)
        bad = [n for n, f, partial in self.constraints if (partial or complete) and not f(m)]
        for i in state:
            bad += self.site_violations(i)
        return bad

    def is_solution(self, state):
        return len(state) > 0 and not self.violations(state, complete=True)
