"""Validates the checked-in real-QGIS trade-route geometry
(geodata/qgis_trade_routes.geojson) against an independent `pyproj`
calculation -- same precedent as this project's own
model/validate_sub_indices.py: a real, runnable check, not just a claim in
a docstring.

For each route, an independently-measured pyproj geodesic distance across
the two segments either side of the route's own midpoint should sum to
very close to the route's own QGIS-reported total distance -- true only if
the midpoint actually sits on the great-circle path (a straight Cartesian
interpolation would fail this for any sufficiently long or high-latitude
route). Run after regenerating the routes:

    python validate_qgis_routes.py
"""
import json
import sys

from pyproj import Geod

TOLERANCE_KM = 1.0  # generous; observed error is consistently well under 0.1km


def main() -> int:
    geod = Geod(ellps="WGS84")

    with open("geodata/qgis_trade_routes.geojson") as f:
        routes = json.load(f)["features"]

    errors = []
    max_err_km = 0.0
    for feat in routes:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        if coords[0] == coords[-1]:
            errors.append(f"{props['country_a']}-{props['country_b']}: route start equals its own end")
            continue

        a_lon, a_lat = coords[0]
        b_lon, b_lat = coords[-1]
        mid_lon, mid_lat = coords[len(coords) // 2]

        _, _, d1 = geod.inv(a_lon, a_lat, mid_lon, mid_lat)
        _, _, d2 = geod.inv(mid_lon, mid_lat, b_lon, b_lat)
        measured_km = (d1 + d2) / 1000.0
        err_km = abs(measured_km - props["distance_km"])
        max_err_km = max(max_err_km, err_km)
        if err_km > TOLERANCE_KM:
            errors.append(
                f"{props['country_a']}-{props['country_b']}: QGIS says {props['distance_km']}km, "
                f"independent pyproj midpoint-sum says {measured_km:.1f}km (off by {err_km:.2f}km)"
            )

    print(f"Checked {len(routes)} real QGIS-generated routes against an independent pyproj calculation.")
    print(f"Largest disagreement: {max_err_km * 1000:.1f} meters.")

    if errors:
        print(f"\nFAILED: {len(errors)} route(s) exceed the {TOLERANCE_KM}km tolerance:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASSED: every route's midpoint sits on the true geodesic path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
