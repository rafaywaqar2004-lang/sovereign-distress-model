"""
Fetch real, public-domain world country boundary polygons (Natural Earth
110m admin-0 countries) and trim them to the app's map viewport.

Run via GitHub Actions, not locally -- this sandbox blocks direct outbound
requests to raw.githubusercontent.com, same as every other real external
fetch in this project.

Why bundle this at all instead of letting Plotly load its own basemap:
Plotly's built-in `scope="world"` choropleth fetches its country-boundary
topojson from cdn.plot.ly at render time, in the *viewer's* browser. That's
an extra runtime dependency for every visitor (and it happens to be a CDN
this sandbox can't reach either, which is how this was caught -- the map
rendered blank here with a real "unexpected error while fetching topojson
file at https://cdn.plot.ly/un/world_110m.json" console error). Bundling
the polygons directly into the app's own data removes that dependency
entirely, for this sandbox and for every real visitor alike.
"""
import json
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)
# Real finding from the first pass at 110m resolution: Natural Earth's 110m
# dataset drops small states entirely below a certain land area -- Bahrain
# and the Maldives, both tracked countries in this project's own 34-country
# panel, were silently missing from the fetched result. Switched to the 50m
# dataset, which does include them, rather than ship a "detailed map" with
# two of the 34 tracked countries invisible on it.

# Our map's viewport (see app.py: lataxis_range / lonaxis_range) covers
# North Africa, the Middle East, and South/Central Asia -- roughly the
# same window MENASA and this project already track, plus a small margin
# so neighboring countries render as visible geographic context.
LAT_RANGE = (-12, 46)
LON_RANGE = (-24, 98)


def bbox_overlaps(geom, lat_range, lon_range):
    coords_flat = []

    def walk(c):
        if isinstance(c[0], (int, float)):
            coords_flat.append(c)
        else:
            for sub in c:
                walk(sub)

    walk(geom["coordinates"])
    if not coords_flat:
        return False
    lons = [c[0] for c in coords_flat]
    lats = [c[1] for c in coords_flat]
    return (
        max(lons) >= lon_range[0] and min(lons) <= lon_range[1]
        and max(lats) >= lat_range[0] and min(lats) <= lat_range[1]
    )


def main():
    print(f"Fetching {SOURCE_URL} ...")
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:
        raw = json.load(resp)
    print(f"Real fetch returned {len(raw['features'])} countries (full world).")

    kept = []
    for feat in raw["features"]:
        if not bbox_overlaps(feat["geometry"], LAT_RANGE, LON_RANGE):
            continue
        props = feat["properties"]
        kept.append({
            "type": "Feature",
            "properties": {
                "ADM0_A3": props.get("ADM0_A3"),
                "NAME": props.get("NAME"),
            },
            "geometry": feat["geometry"],
        })

    trimmed = {"type": "FeatureCollection", "features": kept}
    with open("countries.geojson", "w") as f:
        json.dump(trimmed, f, separators=(",", ":"))

    print(f"Trimmed to {len(kept)} countries within the app's map viewport.")
    print(f"Sample codes: {[f['properties']['ADM0_A3'] for f in kept[:10]]}")


if __name__ == "__main__":
    main()
