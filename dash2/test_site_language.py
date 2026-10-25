"""Language changes are restricted to display text, never values or identities."""
import copy
import json
import unittest

from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase

from .locale_middleware import SiteLanguageMiddleware
from .site_language import figure, nodes, payload, translate


class TranslationTests(unittest.TestCase):
    def test_default_and_dynamic_messages(self):
        self.assertEqual(translate("Predicciones"), "Predicciones")
        self.assertEqual(translate("Predicciones", "en"), "Predictions")
        self.assertEqual(translate("Todo el año 2025", "en"), "Full year 2025")
        self.assertEqual(translate("De 1.160 sectores del mapa", "en"), "Out of 1,160 map sectors")
        self.assertEqual(translate("7 días anteriores", "en"), "Previous 7 days")
        self.assertEqual(translate("Fechas de reporte: 03/02/2025 – 09/02/2025.", "en"), "Report dates: 2025-02-03 – 2025-02-09.")
        self.assertEqual(translate("03/02/2025", "es"), "03/02/2025")
        self.assertEqual(translate("Móvil Fontibón", "en"), "Móvil Fontibón")

    def test_options_keep_values_and_component_identity(self):
        component = {"namespace": "dash_core_components", "type": "Dropdown", "props": {
            "id": "frecuency", "value": "Diaria", "options": ["Diaria", "Semanal", "Mensual"]}}
        translated = nodes(component, "en")
        self.assertEqual(translated["props"]["id"], "frecuency")
        self.assertEqual(translated["props"]["value"], "Diaria")
        self.assertEqual(translated["props"]["options"], [
            {"label": "Daily", "value": "Diaria"}, {"label": "Weekly", "value": "Semanal"}, {"label": "Monthly", "value": "Mensual"}])
        self.assertEqual(component["props"]["options"], ["Diaria", "Semanal", "Mensual"])

    def test_figure_keeps_measurements_geometry_and_units(self):
        source = {"data": [{"type": "scatter", "x": [1, 2], "y": [10.5, 20.5], "name": "Temperatura",
            "customdata": [["Móvil Fontibón", "Relleno de hueco corto", 3]],
            "hovertemplate": "%{y:.2f} °C · Temperatura", "marker": {"color": "#827b10"}}],
            "layout": {"title": {"text": "Promedio"}, "xaxis": {"range": [1, 2]}, "meta": {"dataset_mode": "estimated"}}}
        before = copy.deepcopy(source)
        translated = figure(source, "en")
        self.assertEqual(translated["data"][0]["x"], [1, 2])
        self.assertEqual(translated["data"][0]["y"], [10.5, 20.5])
        self.assertEqual(translated["data"][0]["marker"], source["data"][0]["marker"])
        self.assertEqual(translated["layout"]["meta"], source["layout"]["meta"])
        self.assertEqual(translated["data"][0]["name"], "Temperature")
        self.assertEqual(translated["data"][0]["customdata"], [["Móvil Fontibón", "Short-gap fill", 3]])
        self.assertIn("%{y:.2f} °C", translated["data"][0]["hovertemplate"])
        self.assertEqual(source, before)

    def test_patches_translate_display_fields_only(self):
        patch = {"__dash_patch_update": "__dash_patch_update", "operations": [
            {"operation": "Assign", "location": ["data", 1, "hovertemplate"], "params": {"value": "Temperatura: %{z} °C"}},
            {"operation": "Assign", "location": ["data", 1, "z"], "params": {"value": [1.5, 3.5]}},
            {"operation": "Assign", "location": ["layout", "meta"], "params": {"value": {"dataset_mode": "estimated"}}}]}
        translated = figure(patch, "en")
        self.assertEqual(translated["operations"][0]["params"]["value"], "Temperature: %{z} °C")
        self.assertEqual(translated["operations"][1:], patch["operations"][1:])

    def test_callbacks_translate_children_and_keep_store_data(self):
        response = {"response": {
            "summary": {"children": "Usme · 168 mediciones"},
            "selected-neighborhoods": {"data": ["EL MADRIGAL, 005635 (299)"]},
            "frecuency": {"value": "Diaria"}}}
        result = payload(response, "en")
        self.assertEqual(result["response"]["summary"]["children"], "Usme · 168 measurements")
        self.assertEqual(result["response"]["selected-neighborhoods"], response["response"]["selected-neighborhoods"])
        self.assertEqual(result["response"]["frecuency"]["value"], "Diaria")


class LocaleMiddlewareTests(SimpleTestCase):
    def test_iframe_referer_selects_callback_language(self):
        request = RequestFactory().post("/django_plotly_dash/app/Test/_dash-update-component",
            HTTP_REFERER="http://127.0.0.1:5173/django_plotly_dash/app/Test/?lang=en")
        middleware = SiteLanguageMiddleware(lambda _: JsonResponse({"response": {"label": {"children": "Mes"}}}))
        response = middleware(request)
        self.assertEqual(json.loads(response.content)["response"]["label"]["children"], "Month")
        self.assertEqual(response["Content-Language"], "en")

    def test_missing_or_unsupported_language_defaults_to_spanish(self):
        for query in ["", "?lang=unsupported"]:
            request = RequestFactory().get("/django_plotly_dash/app/Test/_dash-layout" + query)
            middleware = SiteLanguageMiddleware(lambda _: JsonResponse({"namespace": "dash_html_components", "type": "P", "props": {"children": "Mes"}}))
            response = middleware(request)
            self.assertEqual(json.loads(response.content)["props"]["children"], "Mes")
            self.assertEqual(response["Content-Language"], "es")

    def test_data_endpoints_and_downloads_are_not_translated(self):
        source = '{"value":"Diaria","station":"Móvil Fontibón"}'.encode("utf-8")
        request = RequestFactory().get("/api/predictions/query/?lang=en")
        response = SiteLanguageMiddleware(lambda _: HttpResponse(source, content_type="application/json"))(request)
        self.assertEqual(response.content, source)
