"""Small read-only endpoints for the cycling planner; no trip persistence."""
from pathlib import Path
import logging

from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_GET
import plotly

from . import planner

logger = logging.getLogger(__name__)


def respond(operation):
    try:
        return JsonResponse(operation(), json_dumps_params={"ensure_ascii": False, "allow_nan": False})
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except planner.ProviderUnavailable as error:
        return JsonResponse({"error": str(error)}, status=503)
    except (OSError, KeyError, TypeError):
        logger.exception("Cycling planner data unavailable")
        return JsonResponse({"error": "data_unavailable"}, status=503)


@require_GET
def places(request):
    return respond(lambda: {"places": planner.search_places(request.GET.get("q", ""))})


@require_GET
def compare(request):
    return respond(lambda: planner.plan(request.GET))


@require_GET
def plotly_bundle(request):
    response = FileResponse((Path(plotly.__file__).parent / "package_data/plotly.min.js").open("rb"), content_type="text/javascript")
    response["Cache-Control"] = "public, max-age=86400"
    return response
