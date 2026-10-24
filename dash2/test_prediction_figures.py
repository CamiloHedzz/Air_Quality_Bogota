"""Comprobar cifras, ausencias y callbacks de los gráficos interactivos."""
import csv
import io
from urllib.parse import urlencode

from django.test import SimpleTestCase, TestCase
import numpy as np
import pandas as pd

from dash2 import prediction_data as data
from dash2 import prediction_figures as plots
from dash2.prediction_dash import update_plot


class PredictionFigureTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = {"station": "5", "variable": "pm_25", "view": "diagnostics", "horizon": "24",
                      "history": "7", "aggregation": "hour", "statistic": "mean", "comparison": "11", "related": "humidity"}
        options = data.options(cls.params)
        cls.params["date"] = options["dates"][-1]
        cls.params["hour"] = options["hours"][cls.params["date"]][-1]

    def test_diagnostics_metrics_are_computed_on_published_predictions(self):
        response = self.client.get('/api/predictions/query/', self.params)
        self.assertEqual(response.status_code, 200)
        actual = response.json()['diagnostics']
        part = plots.evaluation('5', 'pm_25', 24)
        errors = part.y_pred - part.y_true
        self.assertEqual(actual['n'], len(part))
        self.assertAlmostEqual(actual['mae'], errors.abs().mean())
        self.assertAlmostEqual(actual['bias'], errors.mean())
        self.assertAlmostEqual(actual['rmse'], np.sqrt((errors ** 2).mean()))
        self.assertEqual(self.client.get('/api/predictions/options/', self.params | {'variable': 'humidity'}).status_code, 400)

    def test_parity_and_histogram_use_signed_actual_errors(self):
        part = plots.evaluation('5', 'pm_25', 24)
        figure, caption = plots.render(self.params, 'parity')
        np.testing.assert_allclose(figure.data[0].x, part.y_true)
        np.testing.assert_allclose(figure.data[0].y, part.y_pred)
        np.testing.assert_allclose(figure.data[1].x, figure.data[1].y)
        self.assertEqual(len(figure.data[2].x), 1)
        self.assertIn(str(len(part)), caption)
        figure, _ = plots.render(self.params, 'residual')
        self.assertEqual(figure.data[0].type, 'histogram')
        np.testing.assert_allclose(figure.data[0].x, part.y_pred - part.y_true)

    def test_horizons_and_boxes_compare_identical_observed_targets(self):
        groups = {h: plots.evaluation('5', 'pm_25', h).set_index('target_datetime') for h in (24, 48, 72)}
        common = groups[24].index.intersection(groups[48].index).intersection(groups[72].index)
        figure, caption = plots.render(self.params, 'horizon')
        self.assertEqual(len(figure.data), 2)
        self.assertIn(str(len(common)), caption)
        for trace, column in zip(figure.data, ['y_pred', 'baseline']):
            expected = [(groups[h].loc[common, column] - groups[h].loc[common, 'y_true']).abs().mean() for h in (24, 48, 72)]
            np.testing.assert_allclose(trace.y, expected)
        figure, caption = plots.render(self.params, 'box')
        for trace, horizon in zip(figure.data, (24, 48, 72)):
            self.assertEqual(trace.type, 'box')
            np.testing.assert_allclose(trace.y, groups[horizon].loc[common, 'y_pred'] - groups[horizon].loc[common, 'y_true'])
        self.assertIn('No es un intervalo', caption)

    def test_timeline_has_real_forecast_and_does_not_connect_gaps(self):
        params = self.params | {'view': 'evolution', 'show_observed': '0', 'history': '90'}
        result = data.query_result(params)
        figure, _ = plots.render(params)
        self.assertFalse(figure.data[0].connectgaps)
        self.assertIn(None, figure.data[0].y)
        self.assertEqual(figure.data[1].y[0], result['forecast']['value'])
        self.assertEqual(figure.data[-1].visible, 'legendonly')
        self.assertEqual(pd.Timestamp(figure.data[1].x[0]), plots.local_time(result['forecast']['time']))

    def test_heatmap_preserves_missing_and_scatter_has_actual_pairs(self):
        params = self.params | {'view': 'hourly'}
        available = data.options(params)
        params['date'] = available['dates'][0]
        params['hour'] = available['hours'][params['date']][-1]
        result = data.query_result(params)
        figure, _ = plots.render(params)
        self.assertEqual(figure.data[0].type, 'heatmap')
        self.assertEqual(sum(value is None for row in figure.data[0].z for value in row), sum(p['value'] is None for p in result['heatmap']))
        params = self.params | {'view': 'relationship'}
        result = data.query_result(params)
        figure, _ = plots.render(params)
        self.assertEqual(len(figure.data[0].x), len(result['scatter']))

    def test_evaluation_export_contains_all_horizons_and_signed_errors(self):
        response = self.client.get('/api/predictions/export/', self.params | {'kind': 'evaluation'})
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual({row['horizon_hours'] for row in rows}, {'24', '48', '72'})
        expected_count = sum(len(plots.evaluation('5', 'pm_25', h)) for h in (24, 48, 72))
        self.assertEqual(len(rows), expected_count)
        for row in rows:
            self.assertAlmostEqual(float(row['error']), float(row['y_pred']) - float(row['y_true']))
            self.assertTrue(row['target_source_sha256'])

    def test_dash_registered_callback_and_invalid_selection(self):
        figure, caption, style = update_plot('?' + urlencode(self.params), 'parity')
        self.assertEqual(len(figure.data), 3)
        self.assertEqual(style, {})
        figure, caption, style = update_plot('?' + urlencode(self.params | {'station': 'invalid'}), 'parity')
        self.assertEqual(len(figure.data), 0)
        self.assertIn('Revisa', caption)


class PredictionDashRouteTests(TestCase):
    def test_registered_dash_can_open_with_an_isolated_database(self):
        self.assertEqual(self.client.get('/django_plotly_dash/app/PredictionCharts/').status_code, 200)
