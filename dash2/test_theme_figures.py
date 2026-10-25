"""The site theme changes presentation without changing the mapped measurements."""
import unittest

import pandas as pd

from dash2.dash_figures import BASEMAPS, get_figure
from dash2.neighborhood_data import figure_update


class ThemeFigureTests(unittest.TestCase):
    def figure(self, basemap):
        data = pd.DataFrame({"neighborhood": ["Sector A"], "pm_25_mean": [12.5]})
        return get_figure(data, "pm_25_mean", {"type": "FeatureCollection", "features": []}, basemap=basemap)

    def test_only_automatic_basemap_tracks_site_theme(self):
        self.assertTrue(self.figure("auto").layout.meta["airqualityAutoBasemap"])
        for basemap in ["color", "light", "dark"]:
            figure = self.figure(basemap)
            self.assertFalse(figure.layout.meta["airqualityAutoBasemap"])
            self.assertEqual(figure.layout.mapbox.style, BASEMAPS[basemap])
            self.assertEqual(list(figure.data[0].z), [12.5])

    def test_partial_map_updates_carry_the_theme_mode(self):
        figure = self.figure("auto")
        figure.add_trace(figure.data[0])
        patch = figure_update(figure).to_plotly_json()["operations"]
        metadata = [operation for operation in patch if operation["location"] == ["layout", "meta"]]
        self.assertEqual(metadata[0]["params"]["value"], {"airqualityAutoBasemap": True})
        self.assertFalse(any("geojson" in operation["location"] for operation in patch))
