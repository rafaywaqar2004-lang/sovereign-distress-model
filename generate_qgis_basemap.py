"""Renders the Trade & Geopolitical Shocks route map's background as a real
QGIS map render (QgsMapSettings + QgsMapRendererParallelJob), replacing the
faint white country_outline_traces() line traces that were purely
orientational, not data.

Uses the same bundled map-data/countries.geojson the Coverage map (tab1)
already uses -- no new geographic data, just a higher-quality, project-styled
render of it, in this project's own dark teal/orange palette (app.py's
SURFACE_ALT/ACCENT/BG constants).

Offline/build-time step: output is checked into
static/route_map_basemap.png; app.py places it as a Plotly background image
(fig.add_layout_image) at the exact same lon/lat extent (x=[-24,98],
y=[-12,46]) the Coverage map and route lines already use, so QGIS's render
and Plotly's route/marker data line up pixel-for-pixel. QGIS itself is not a
runtime dependency of the deployed app -- only the static PNG is.

Run with the Python QGIS was built against (e.g. /usr/bin/python3.12 on
Ubuntu 24.04 with the qgis apt package):

    QT_QPA_PLATFORM=offscreen /usr/bin/python3.12 generate_qgis_basemap.py
"""
from __future__ import annotations

from pathlib import Path

# Must match app.py's fig_routes.update_xaxes/update_yaxes range exactly
# (the same fixed viewport the Coverage map on tab1 already established for
# these 34 tracked economies), or the image will not align with the route
# lines plotted on it.
LON_RANGE = (-24, 98)
LAT_RANGE = (-12, 46)

# This project's own dark palette (app.py) -- land reads as the same
# SURFACE_ALT tone cards/panels use, water matches the plot's own BG so the
# basemap blends seamlessly into the page rather than looking like a pasted
# rectangle, and the accent-teal route lines/markers stay the highest-
# contrast thing on the map.
LAND_FILL = "#152420"    # SURFACE_ALT
LAND_BORDER = "#2E453F"  # a shade lighter than SURFACE_ALT, for a visible coastline without competing with ACCENT
WATER_FILL = "#0A1211"   # BG -- matches fig_routes' own plot_bgcolor exactly

OUTPUT_WIDTH = 1600
OUTPUT_HEIGHT = round(OUTPUT_WIDTH * (LAT_RANGE[1] - LAT_RANGE[0]) / (LON_RANGE[1] - LON_RANGE[0]))


def main() -> None:
    from qgis.core import (
        QgsApplication,
        QgsCoordinateReferenceSystem,
        QgsFillSymbol,
        QgsMapSettings,
        QgsMapRendererParallelJob,
        QgsRectangle,
        QgsVectorLayer,
    )
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor

    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        repo_root = Path(__file__).resolve().parent
        geojson_path = repo_root / "map-data" / "countries.geojson"

        layer = QgsVectorLayer(str(geojson_path), "countries", "ogr")
        if not layer.isValid():
            raise RuntimeError(f"Failed to load {geojson_path} as a QGIS vector layer")

        symbol = QgsFillSymbol.createSimple(
            {
                "color": LAND_FILL,
                "outline_color": LAND_BORDER,
                "outline_width": "0.4",
                "outline_width_unit": "MM",
            }
        )
        layer.renderer().setSymbol(symbol)

        settings = QgsMapSettings()
        settings.setLayers([layer])
        settings.setBackgroundColor(QColor(WATER_FILL))
        settings.setOutputSize(QSize(OUTPUT_WIDTH, OUTPUT_HEIGHT))
        settings.setExtent(QgsRectangle(LON_RANGE[0], LAT_RANGE[0], LON_RANGE[1], LAT_RANGE[1]))
        settings.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        settings.setOutputDpi(96)
        settings.setFlag(QgsMapSettings.Antialiasing, True)

        job = QgsMapRendererParallelJob(settings)
        job.start()
        job.waitForFinished()

        image = job.renderedImage()
        out_dir = repo_root / "static"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "route_map_basemap.png"
        image.save(str(out_path), "PNG")
        print(f"Wrote {OUTPUT_WIDTH}x{OUTPUT_HEIGHT} QGIS basemap render to {out_path}")

    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    main()
