"""Select the iframe's language for Dash layouts and callback display text."""
import json
from urllib.parse import parse_qs, urlparse

from .site_language import payload


class SiteLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith("/django_plotly_dash/") or not request.path.rstrip("/").endswith(("_dash-layout", "_dash-update-component")):
            return response
        if response.status_code != 200 or response.streaming or "application/json" not in response.get("Content-Type", ""):
            return response
        language = request.GET.get("lang")
        if language is None:
            language = parse_qs(urlparse(request.META.get("HTTP_REFERER", "")).query).get("lang", ["es"])[-1]
        language = "en" if language == "en" else "es"
        data = json.loads(response.content)
        response.content = json.dumps(payload(data, language), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        response["Content-Length"] = str(len(response.content))
        response["Content-Language"] = language
        # A layout/callback contains translated labels and must not be reused for another language.
        response["Cache-Control"] = "no-store"
        return response
