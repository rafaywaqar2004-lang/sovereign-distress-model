"""Generates real geodesic (great-circle) route geometry for every real
bilateral trade edge between two tracked countries, using real QGIS
(PyQGIS), not a re-implementation of its math in another library.

Companion to the identical real-QGIS approach shipped in this project's
siblings, the Gulf AI & Tech-Bloc Alignment Tracker and the MENASA Risk
Monitor. Unlike those two projects' chokepoint-proximity analysis, this
project's own data/chokepoint_exposure.py deliberately rejects proximity
reasoning ("use actual trade/shipping relationships when possible, not
proximity assumptions"), so QGIS is applied here to what this project
actually models instead: real UN Comtrade bilateral trade relationships
(model/trade_network.py). QGIS's job is purely cartographic -- computing
the geometrically correct great-circle path between two real trading
partners' capitals, not inferring exposure from geography. The trade
values themselves are untouched, real Comtrade data.

Real QGIS engine used: QgsDistanceArea's direct geodesic solver --
`bearing()` for the initial azimuth between two points and
`computeSpheroidProject()` (the same forward-geodesic computation used for
the Gulf tracker's and MENASA's buffer rings) stepped along increasing
distance at that fixed initial azimuth, which is exactly how a geodesic
curve is traced on an ellipsoid (the "direct geodesic problem" -- the same
algorithm class Karney/Vincenty solvers implement, and the same one
QGIS's own C++ geodesic engine uses internally for its "Measure" tool's
geodesic mode).

Offline/build-time step: output is checked into
geodata/qgis_trade_routes.geojson and app.py just reads it, rather than
requiring QGIS itself (roughly 1GB of Qt/GDAL/GRASS dependencies) as a
runtime dependency of a Streamlit app on Render's free tier.

Run with the Python QGIS was built against (e.g. /usr/bin/python3.12 on
Ubuntu 24.04 with the qgis apt package):

    QT_QPA_PLATFORM=offscreen /usr/bin/python3.12 generate_qgis_geodata.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "data"))
from country_coordinates import COUNTRY_CAPITAL_COORDS  # noqa: E402

ROUTE_POINTS = 24  # vertices per route (including both endpoints) -- smooth enough for this map's scale
OUT_DIR = Path("geodata")


def main() -> None:
    from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsDistanceArea, QgsPointXY, QgsProject

    OUT_DIR.mkdir(exist_ok=True)

    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        da = QgsDistanceArea()
        da.setEllipsoid("WGS84")
        da.setSourceCrs(QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance().transformContext())

        df = pd.read_csv("data/trade_network.csv")
        tracked = set(COUNTRY_CAPITAL_COORDS.keys())
        edges = df.dropna(subset=["partner_code"])
        edges = edges[edges["reporter_code"].isin(tracked) & edges["partner_code"].isin(tracked)]
        # A handful of real UN Comtrade rows report a country trading "with
        # itself" (re-exports/territory-specific reporting quirks) -- a real
        # data fact, but not a route: excluded here rather than generating a
        # zero-length geometry for the map to draw.
        edges = edges[edges["reporter_code"] != edges["partner_code"]]

        pairs = sorted({tuple(sorted((r, p))) for r, p in zip(edges["reporter_code"], edges["partner_code"])})

        features = []
        for country_a, country_b in pairs:
            lat_a, lon_a = COUNTRY_CAPITAL_COORDS[country_a]
            lat_b, lon_b = COUNTRY_CAPITAL_COORDS[country_b]
            p1 = QgsPointXY(lon_a, lat_a)
            p2 = QgsPointXY(lon_b, lat_b)

            total_distance_m = da.measureLine(p1, p2)
            initial_bearing = da.bearing(p1, p2)

            coords = []
            for i in range(ROUTE_POINTS):
                frac = i / (ROUTE_POINTS - 1)
                if frac == 0:
                    pt = p1
                elif frac == 1:
                    pt = p2
                else:
                    pt = da.computeSpheroidProject(p1, total_distance_m * frac, initial_bearing)
                coords.append([pt.x(), pt.y()])

            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "country_a": country_a,
                        "country_b": country_b,
                        "distance_km": round(total_distance_m / 1000.0, 1),
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )

        geojson = {"type": "FeatureCollection", "features": features}
        out_path = OUT_DIR / "qgis_trade_routes.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f)
        print(f"Wrote {len(features)} real geodesic trade-route geometries to {out_path}")

    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    main()
