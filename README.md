# VoltRoute AI — Intelligent EV Charging Station Allocation Agent

## Problem statement
Cities must decide where to install a limited number of EV chargers given demand, cost, grid capacity and distance.

## Objective
Recommend an EV charging network that satisfies all hard constraints (budget, max stations, grid, capacity, distance, coverage) while balancing coverage, cost, distance and grid load.

## Features
- "Living Energy Map" UI: landing page with miniature-city hero, 8-step "Run Allocation" sequence
- 8 pages: Overview, EV Demand, Candidate Sites, Constraints, AI Search, Optimization, Algorithms, Results
- Interactive Folium map (works offline; plotly fallback), Plotly charts, CSV download
- Friendly errors for missing/empty data, invalid input and impossible constraints

## AI concepts used (all real code in `ai/`)
| Concept | File |
|---|---|
| Intelligent Agent | `agent.py` |
| Problem Formulation / State Space | `problem_formulation.py` |
| Heuristic function H = w1·distance + w2·cost + w3·unserved + w4·grid | `heuristics.py` |
| A* search, f = g + h | `astar.py` |
| CSP (variables = sites, domain = {selected, not}) | `csp.py` |
| Constraint propagation (unary pruning + dominance) | `constraint_propagation.py` |
| Backtracking search | `backtracking.py` |
| Local search (hill climbing: add/remove/replace) | `local_search.py` |
| Optimization (normalised 0–100 score) | `optimizer.py` |

## System architecture / algorithm flow
Real-world problem → Problem formulation → Agent → Candidate states → CSP → Constraint propagation → Heuristic → A* → Backtracking → Local search → Optimization → Recommended network.
The better of the A* and backtracking solutions is improved by hill climbing; the result is always re-checked against the hard constraints.

## Dataset (`data/`)
- `ev_locations.csv` — 20 synthetic Chennai candidate sites (cost in ₹ lakh, capacity/grid in kW, land availability, distance to existing station)
- `demand_zones.csv` — 8 demand zones (relative demand, scaled to the "Total EV demand" input)
- `existing_stations.csv` — 8 existing stations

Model: a zone is covered if a selected station is within the max distance; 1 kW serves 1.5 EVs/day.

## Installation
```
pip install -r requirements.txt
```
## How to run
```
streamlit run app.py
```
(Windows: double-click `run.bat`; Linux/macOS: `./run.sh`.) Self-test: `python tests/test_pipeline.py`

## Example usage / expected output
Defaults (₹50L, 6 stations, 5 km, 85% coverage): ~4 stations, ~94% coverage, ~₹42L, in well under a second, with states explored, backtracks and improvement % shown on the AI Search / Optimization pages. Try budget = 5 to see the "No feasible charging network…" message.

## Future scope
Real map/road distances, time-of-day demand, user-uploaded CSVs, simulated annealing / genetic algorithm comparison.
