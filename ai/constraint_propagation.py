"""Constraint propagation: remove infeasible / dominated candidates before search."""


def propagate(pr, csp):
    p, sites = pr.p, pr.sites
    initial = len(pr.cand)
    pruned, kept = [], []
    # Pass 1: node consistency (unary constraints)
    for i in pr.cand:
        name = sites.loc[i, "location_name"]
        sv = csp.site_violations(i)
        if str(sites.loc[i, "land_availability"]).strip().lower() not in ("yes", "y", "1", "true"):
            pruned.append((name, "Land unavailable"))
        elif pr.cost[i] > p.budget:
            pruned.append((name, "Installation cost exceeds budget"))
        elif pr.kw[i] > p.grid_limit:
            pruned.append((name, "Station load exceeds grid limit"))
        elif sites.loc[i, "existing_station_distance"] < 0.5:
            pruned.append((name, "Too close to an existing station"))
        elif sv:
            pruned.append((name, sv[0] + " violated"))
        else:
            kept.append(i)

    def zones_of(i):
        return {j for j, d in enumerate(pr.dist[i]) if d <= p.max_distance}
    # Pass 2: dominance - A is dropped if B covers all zones of A, costs no more, has no less capacity
    final = []
    for a in kept:
        dom = None
        for b in kept:
            if b != a and zones_of(a) <= zones_of(b) and pr.cost[b] <= pr.cost[a] and pr.kw[b] >= pr.kw[a] \
                    and (zones_of(a) != zones_of(b) or pr.cost[b] < pr.cost[a] or pr.kw[b] > pr.kw[a] or b < a):
                dom = b
                break
        if dom is None:
            final.append(a)
        else:
            pruned.append((sites.loc[a, "location_name"], f"Dominated by {sites.loc[dom, 'location_name']}"))
    pr.cand = final
    csp.variables = list(final)
    csp.domains = {v: (1, 0) for v in final}
    return dict(initial=initial, remaining=len(final), pruned_count=initial - len(final), pruned=pruned)
