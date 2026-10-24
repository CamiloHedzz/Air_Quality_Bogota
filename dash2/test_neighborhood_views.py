import gzip
import hashlib
import json
from django.test import SimpleTestCase
from dash2 import neighborhood_data as maps


class NeighborhoodDownloadTests(SimpleTestCase):
    def test_geometry_has_original_bytes_version_and_browser_cache(self):
        digest=maps.load_history()[2]['input_sha256']['dash2/datasets/bogota_cadastral.json']
        response=self.client.get('/api/maps/geometry/',{'v':digest[:16]})
        content=b''.join(response.streaming_content)
        self.assertEqual(hashlib.sha256(content).hexdigest(),digest)
        self.assertIn('immutable',response['Cache-Control'])
        cached=self.client.get('/api/maps/geometry/',HTTP_IF_NONE_MATCH=response['ETag'])
        self.assertEqual(cached.status_code,304)
        response.close()

    def test_calendar_download_identifies_estimates(self):
        response=self.client.get('/api/maps/calendar/')
        content=gzip.decompress(b''.join(response.streaming_content)).decode('utf-8')
        self.assertIn('pm_25_origin',content.splitlines()[0])
        self.assertIn('pm_25_short_gap',content.splitlines()[0])
        self.assertIn('knn_scenario_baseline',content)
        self.assertIn('observed_daily_aggregate',content)
        response.close()

    def test_downloaded_notebook_has_executed_cells(self):
        response=self.client.get('/api/maps/methodology/')
        book=json.loads(b''.join(response.streaming_content))
        code=[cell for cell in book['cells'] if cell['cell_type']=='code']
        self.assertTrue(all(cell['execution_count'] for cell in code))
        self.assertFalse(any(output.get('output_type')=='error' for cell in code for output in cell['outputs']))
        response.close()


    def test_original_route_chart_retains_additional_variables(self):
        from dash2.static.pages import dashboard
        name=dashboard.samples.neighborhood.value_counts().index[0]
        figure,bars,*styles=dashboard.update_regression_figure([name],'pm_25_mean',2024,'all',['pm_25','temperature'],'Diaria','legacy')
        self.assertTrue(any('temperature' in trace.name for trace in figure.data))
        self.assertTrue(len(bars.data))


    def test_source_change_does_not_overwrite_a_newer_valid_filter_selection(self):
        from dash import no_update
        from dash2.static.pages import dashboard
        self.assertIs(dashboard.update_map_years('estimated',2015)[1],no_update)
        self.assertIs(dashboard.update_month_options(2015,'estimated',8)[1],no_update)
        self.assertEqual(dashboard.update_map_years('legacy',2015)[1],2024)


    def test_original_map_values_are_preserved_with_all_boundaries(self):
        import numpy as np
        from dash2.static.pages import dashboard
        data=dashboard.aggregate_neighborhoods(dashboard.filter_period(dashboard.samples,2024))
        figure=maps.map_figure(data,'pm_25_mean',dashboard.counties,mode='legacy')
        actual=dict(zip(figure.data[1].locations,figure.data[1].z))
        self.assertEqual(len(figure.data[0].locations),1160)
        self.assertEqual(len(figure.data[1].locations),1160)
        np.testing.assert_allclose([actual[name] for name in data.neighborhood],data.pm_25_mean)
        self.assertEqual(figure.data[1].meta['dataset_mode'],'legacy')
