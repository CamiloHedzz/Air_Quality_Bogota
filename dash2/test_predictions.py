"""Integración real del paquete de pronósticos, API y descargas; sin entrenar."""
import csv
import io
import json
from unittest.mock import patch

from django.test import SimpleTestCase
import numpy as np
import pandas as pd

from dash2 import prediction_data


class PredictionApiTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = {"station": "5", "variable": "pm_25", "horizon": "24", "view": "evolution",
                    "history": "7", "aggregation": "hour", "statistic": "mean", "related": "humidity", "comparison": "11"}
        options = prediction_data.options(cls.base)
        cls.base["date"] = options["dates"][-1]
        cls.base["hour"] = options["hours"][cls.base["date"]][-1]

    def test_catalog_exposes_partial_coverage_and_actual_training_scope(self):
        response = self.client.get('/api/predictions/catalog/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['coverage']['complete'])
        self.assertEqual(data['coverage']['report_days'], 100)
        self.assertEqual([y['year'] for y in data['coverage']['years']], list(range(2015, 2026)))
        self.assertIn('2025', data['model']['training_scope'])
        self.assertFalse(data['model']['intervals_available'])

    def test_forecast_is_exact_model_result_and_training_precedes_origin(self):
        response = self.client.get('/api/predictions/query/', self.base)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        data, forecasts, _ = prediction_data.store()
        origin = pd.Timestamp(payload['origin'])
        matching = forecasts.loc[forecasts.station_id.eq('5') & forecasts.datetime.eq(origin) & forecasts.target.eq('pm_25') & forecasts.horizon_hours.eq(24)].iloc[0]
        self.assertEqual(payload['forecast']['value'], matching.y_pred)
        self.assertLess(pd.Timestamp(payload['forecast']['training_end']), origin)
        self.assertEqual(pd.Timestamp(payload['forecast']['time']) - origin, pd.Timedelta(hours=24))
        truth = data.loc[data.station_id.eq('5') & data.datetime.eq(matching.target_datetime)].iloc[0]
        self.assertEqual(payload['forecast']['observed_after'], truth.pm_25)
        self.assertTrue(all(pd.Timestamp(p['time']) <= origin for p in payload['series']))
        self.assertNotIn('NaN', response.content.decode())

    def test_unavailable_date_and_injection_values_are_rejected(self):
        for changes in ({'date': '2026-10-23'}, {'horizon': '999'}, {'station': '../'}, {'history': '100000'}, {'variable': 'bad'}):
            with self.subTest(changes=changes):
                self.assertEqual(self.client.get('/api/predictions/query/', self.base | changes).status_code, 400)
        self.assertEqual(self.client.post('/api/predictions/query/', self.base).status_code, 405)

    def test_climate_and_earlier_years_are_observations_without_fake_forecasts(self):
        params = self.base | {'variable': 'humidity', 'related': 'pm_25'}
        options = prediction_data.options(params)
        self.assertTrue(any(day.startswith('2015') for day in options['dates']))
        params['date'] = next(day for day in options['dates'] if day.startswith('2015'))
        params['hour'] = options['hours'][params['date']][-1]
        result = self.client.get('/api/predictions/query/', params).json()
        self.assertIsNone(result['forecast'])
        self.assertEqual(result['unit'], '%')
        self.assertTrue(any(p['value'] is None for p in result['series']))

    def test_relationship_heatmap_and_pairwise_comparison_are_calculated(self):
        params = self.base | {'view': 'relationship'}
        result = self.client.get('/api/predictions/query/', params).json()
        raw = prediction_data.parse_query(params)['primary'][['pm_25', 'humidity']].dropna()
        self.assertEqual(result['metrics']['paired_values'], len(raw))
        self.assertTrue(np.isclose(result['metrics']['correlation'], raw.pm_25.corr(raw.humidity)))
        self.assertEqual(len(result['heatmap']), 56)
        self.assertEqual(sum(p['n'] for p in result['heatmap']), result['metrics']['observed'])
        comparison = self.client.get('/api/predictions/query/', self.base | {'view': 'comparison'}).json()
        self.assertGreater(comparison['metrics']['comparison_pairs'], 0)
        self.assertIsNone(comparison['forecast'])

    def test_exports_match_observations_and_forecast_and_preserve_missing(self):
        query = prediction_data.parse_query(self.base)
        response = self.client.get('/api/predictions/export/', self.base | {'kind': 'observations'})
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(len(rows), len(query['primary']))
        self.assertIn('source_sha256', rows[0])
        self.assertTrue(all(row['pm_25_origin'] == 'observed' or row['pm_25'] == '' for row in rows))
        response = self.client.get('/api/predictions/export/', self.base | {'kind': 'forecast'})
        row = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))[0]
        self.assertEqual(row['record_type'], 'historical_forecast')
        self.assertAlmostEqual(float(row['forecast']), prediction_data.forecast(query)['value'])

    def test_missing_package_produces_error_without_illustrative_fallback(self):
        with patch('dash2.prediction_data.store', side_effect=FileNotFoundError('missing')):
            response = self.client.get('/api/predictions/catalog/')
        self.assertEqual(response.status_code, 503)
        self.assertIn('error', json.loads(response.content))
        self.assertIsNone(prediction_data.number(np.nan))
        self.assertEqual(prediction_data.number(0), 0)
