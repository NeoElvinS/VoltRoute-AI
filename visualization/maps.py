"""Folium map for CSV-backed Chennai demand and AI allocation results."""
from html import escape

import folium
from branca.element import Element, MacroElement
from jinja2 import Template
from folium.plugins import Fullscreen


CHENNAI_CENTER = [13.0827, 80.2707]
CHENNAI_ZOOM = 11


class ResetChennaiControl(MacroElement):
    _template = Template("""
    {% macro script(this, kwargs) %}
    var {{ this.get_name() }} = L.control({position: 'topleft'});
    {{ this.get_name() }}.onAdd = function(map) {
        var button = L.DomUtil.create('button', 'leaflet-bar');
        button.type = 'button';
        button.title = 'Reset view to Chennai';
        button.setAttribute('aria-label', 'Reset view to Chennai');
        button.innerHTML = 'Reset Chennai';
        button.style.cssText = 'background:#FBF8EF;color:#1F4D36;border:0;padding:0 8px;height:30px;font:12px sans-serif;cursor:pointer';
        L.DomEvent.disableClickPropagation(button);
        L.DomEvent.on(button, 'click', function() { map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }}); });
        return button;
    };
    {{ this.get_name() }}.addTo({{ this._parent.get_name() }});
    {% endmacro %}
    """)

    def __init__(self, center=CHENNAI_CENTER, zoom=CHENNAI_ZOOM):
        super().__init__()
        self._name = "ResetChennaiControl"
        self.lat, self.lon = center
        self.zoom = zoom


def _popup(title, rows):
    details = "".join(
        "<tr><th style='text-align:left;padding:3px 8px 3px 0;color:#59615B'>{}</th>"
        "<td style='padding:3px 0'>{}</td></tr>".format(escape(str(label)), escape(str(value)))
        for label, value in rows
    )
    return ("<div style='min-width:210px;font:13px/1.4 sans-serif;color:#23272A'>"
            "<strong style='display:block;color:#1F4D36;margin-bottom:6px'>{}</strong>"
            "<table>{}</table></div>").format(escape(str(title)), details)


def _legend(has_recommendations):
    entries = [
        ("<span style='background:#D9822B;opacity:.7'></span>", "Demand zones"),
        ("<span style='background:#8C8C84'></span>", "Candidate locations"),
        ("<span style='background:#23272A'></span>", "Existing stations"),
    ]
    if has_recommendations:
        entries.append(("<span style='background:#A6CE39;border:2px solid #1F4D36'></span>", "AI recommended"))
        entries.append(("<i></i>", "Demand assignment"))
    rows = "".join(f"<div class='legend-row'>{mark}{label}</div>" for mark, label in entries)
    return Element("""
    <style>
    .volt-legend { position:absolute; z-index:999; right:12px; bottom:28px; padding:8px 10px;
        background:rgba(251,248,239,.96); border:1px solid #DCD7C9; color:#23272A;
        font:11px/1.6 sans-serif; box-shadow:0 1px 4px rgba(35,39,42,.16); }
      .volt-legend strong { display:block; color:#1F4D36; margin-bottom:3px; }
      .volt-legend .legend-row { white-space:nowrap; }
      .volt-legend span { display:inline-block; width:10px; height:10px; margin-right:7px; border-radius:50%; vertical-align:-1px; }
      .volt-legend i { display:inline-block; width:14px; border-top:2px dashed #1F4D36; margin:0 5px 3px 0; }
    </style>
    <div class='volt-legend'><strong>Map layers</strong>__ROWS__</div>
    """.replace("__ROWS__", rows))


def build_map(pr, existing, state, result=None):
    """Build the map from the formulated CSV data and, when present, the agent result."""
    state = frozenset(state or ())
    m = folium.Map(location=CHENNAI_CENTER, zoom_start=CHENNAI_ZOOM, tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="Street map (internet)", opacity=.55).add_to(m)

    demand_layer = folium.FeatureGroup(name="Demand Zones", show=True).add_to(m)
    candidate_layer = folium.FeatureGroup(name="Candidate Charging Locations", show=True).add_to(m)
    existing_layer = folium.FeatureGroup(name="Existing Charging Stations", show=True).add_to(m)
    recommended_layer = None
    connection_layer = None
    if state:
        recommended_layer = folium.FeatureGroup(name="AI Recommended Stations", show=True).add_to(m)
        connection_layer = folium.FeatureGroup(name="Demand-to-Station Connections", show=True).add_to(m)

    assignments = pr.assign(state) if state else [None] * len(pr.zones)
    assigned_zones = {i: [] for i in range(len(pr.sites))}
    for zone_index, station_index in enumerate(assignments):
        if station_index is not None:
            assigned_zones[station_index].append(zone_index)

    result_rows = {}
    if result:
        result_rows = {row["Location"]: row for row in result.get("table", []).to_dict("records")}
    peak_demand = max(pr.zdem, default=0)

    for zone_index, zone in enumerate(pr.zones.itertuples()):
        demand = pr.zdem[zone_index]
        nearest_index = min(range(len(pr.sites)), key=lambda i: pr.dist[i][zone_index])
        nearest = pr.sites.iloc[nearest_index]
        station_index = assignments[zone_index]
        if station_index is None:
            coverage = "Not allocated" if not state else "Uncovered"
        else:
            coverage = f"Covered by {pr.sites.loc[station_index, 'location_name']}"
        intensity = f"{demand / peak_demand:.0%} of highest-demand zone" if peak_demand else "Unavailable"
        popup = _popup(f"Demand Zone: {zone.zone_name}", [
            ("Zone ID", zone.zone_id),
            ("EV demand", f"{demand:.0f} EVs/day"),
            ("Demand intensity", intensity),
            ("Nearest candidate", f"{nearest.location_name} ({pr.dist[nearest_index][zone_index]:.2f} km)"),
            ("Coverage status", coverage),
        ])
        folium.Circle(
            [zone.latitude, zone.longitude], radius=max(180, demand * 5), color="#D9822B",
            fill=True, fill_color="#D9822B", fill_opacity=.22, weight=1,
            tooltip=f"{zone.zone_name}: {demand:.0f} EVs/day", popup=folium.Popup(popup, max_width=340),
        ).add_to(demand_layer)

        if station_index is not None:
            station = pr.sites.loc[station_index]
            folium.PolyLine(
                [[station.latitude, station.longitude], [zone.latitude, zone.longitude]],
                color="#1F4D36", weight=2, opacity=.72, dash_array="6 5",
                interactive=False,
            ).add_to(connection_layer)

    for site_index, site in pr.sites.iterrows():
        selected = site_index in state
        site_demand = sum(pr.zdem[j] for j in assigned_zones[site_index])
        row = result_rows.get(site["location_name"], {})
        avg_distance = row.get("Distance (km)")
        if avg_distance is None and assigned_zones[site_index]:
            assigned_total = site_demand
            avg_distance = sum(pr.zdem[j] * pr.dist[site_index][j] for j in assigned_zones[site_index]) / assigned_total
        status = "Selected by AI" if selected else "Not selected"
        grid_usage = f"{site.station_capacity} / {site.grid_capacity} kW" if selected else f"0 / {site.grid_capacity} kW allocated"
        candidate_popup = _popup(f"Candidate: {site.location_name}", [
            ("Location", f"{site.latitude:.4f}, {site.longitude:.4f}"),
            ("Installation cost", f"₹{site.installation_cost:.1f} lakh"),
            ("Charging capacity", f"{site.station_capacity} kW"),
            ("Grid capacity / usage", grid_usage),
            ("Demand served", f"{site_demand:.0f} EVs/day" if selected else "Not allocated"),
            ("AI selection", status),
        ])
        folium.CircleMarker(
            [site.latitude, site.longitude], radius=7, color="#59615B", weight=1.5,
            fill=True, fill_color="#8C8C84", fill_opacity=.88,
            tooltip=f"Candidate: {site.location_name}", popup=folium.Popup(candidate_popup, max_width=340),
        ).add_to(candidate_layer)

        if selected:
            reason = row.get("Reason Selected", "Selected in the final AI allocation.")
            rec_popup = _popup(f"AI Recommendation: {site.location_name}", [
                ("AI score", f"{result['score']['score']:.2f} / 100" if result and result.get("score") else "Available in allocation results"),
                ("Demand served", f"{site_demand:.0f} EVs/day"),
                ("Average distance", f"{avg_distance:.2f} km" if avg_distance is not None else "No zones assigned"),
                ("Installation cost", f"₹{site.installation_cost:.1f} lakh"),
                ("Capacity", f"{site.station_capacity} kW"),
                ("Reason for selection", reason),
            ])
            folium.CircleMarker(
                [site.latitude, site.longitude], radius=12, color="#1F4D36", weight=3,
                fill=True, fill_color="#A6CE39", fill_opacity=1,
                tooltip=f"AI recommended: {site.location_name}", popup=folium.Popup(rec_popup, max_width=360),
            ).add_to(recommended_layer)

    for station in existing.itertuples():
        popup = _popup(f"Existing station: {station.station_name}", [
            ("Location", f"{station.latitude:.4f}, {station.longitude:.4f}"),
        ])
        folium.CircleMarker(
            [station.latitude, station.longitude], radius=7, color="#23272A", weight=2,
            fill=True, fill_color="#23272A", fill_opacity=.95,
            tooltip=station.station_name, popup=folium.Popup(popup, max_width=300),
        ).add_to(existing_layer)

    m.add_child(folium.LayerControl(position="topright", collapsed=True))
    Fullscreen(position="topright", title="Expand map", title_cancel="Exit fullscreen").add_to(m)
    ResetChennaiControl().add_to(m)
    m.get_root().html.add_child(_legend(bool(state)))
    return m
