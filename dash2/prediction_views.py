"""API de consulta histórica para el panel de predicciones."""
import csv
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from . import prediction_data

logger = logging.getLogger(__name__)


def respond(operation, request):
    try:
        value = operation(request.GET)
        return JsonResponse(value, json_dumps_params={"ensure_ascii": False, "allow_nan": False})
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except (OSError, KeyError, IndexError) as error:
        logger.exception("No se pudo cargar el paquete histórico de predicciones")
        return JsonResponse({"error": "Los resultados históricos no están disponibles. Intenta de nuevo más tarde."}, status=503)


@require_GET
def catalog(request):
    return respond(lambda _: prediction_data.catalog(), request)


@require_GET
def options(request):
    return respond(prediction_data.options, request)


@require_GET
def query(request):
    return respond(prediction_data.query_result, request)


@require_GET
def export(request):
    try:
        query = prediction_data.parse_query(request.GET)
        kind = request.GET.get("kind", "observations")
        if kind not in {"observations", "forecast", "evaluation"}:
            raise ValueError("Selecciona mediciones, pronóstico o evaluación para descargar.")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{kind}_{query["variable"]}_{query["origin"].date()}.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        if kind == "observations":
            fields = ["datetime", "report_date", "station_id", "station_name", *prediction_data.VARIABLES,
                      *[f"{key}_origin" for key in prediction_data.VARIABLES], "source_url", "source_sha256", "validation_status"]
            writer.writerow(fields + [f"{key}_unit" for key in prediction_data.VARIABLES])
            frame = query["primary"]
            if query["view"] == "comparison":
                frame = query["period"].loc[query["period"].station_id.isin([query["station"], query["comparison"]])]
            for row in frame[fields].fillna("").itertuples(index=False, name=None):
                writer.writerow([*row, *[meta[1] for meta in prediction_data.VARIABLES.values()]])
        elif kind == "evaluation":
            if query["variable"] not in {"pm_25", "pm_10"}:
                raise ValueError("Solo hay evaluación de PM2.5 y PM10.")
            frame = query["forecasts"]
            frame = frame.loc[frame.station_id.eq(query["station"]) & frame.target.eq(query["variable"])].copy()
            frame["error"] = frame.y_pred - frame.y_true
            frame["absolute_error"] = frame.error.abs()
            frame["unit"] = prediction_data.VARIABLES[query["variable"]][1]
            frame["model_version"] = query["model"]["model_version"]
            fields = ["station_id", "target", "unit", "datetime", "target_datetime", "horizon_hours", "y_true", "y_pred", "baseline", "error", "absolute_error", "train_target_max", "model_version", "target_source_url", "target_source_sha256"]
            writer.writerow(fields)
            writer.writerows(frame.sort_values(["target_datetime", "horizon_hours"])[fields].itertuples(index=False, name=None))
        else:
            result = prediction_data.forecast(query)
            if not result:
                raise ValueError("No hay un pronóstico calculado para esta consulta.")
            writer.writerow(["record_type", "model", "model_version", "station_id", "variable", "unit", "origin", "target_datetime",
                             "horizon_hours", "forecast", "persistence", "observed_after", "absolute_error", "training_labels_end", "source_url", "source_sha256"])
            writer.writerow(["historical_forecast", query["model"]["model"], query["model"]["model_version"], query["station"], query["variable"],
                             prediction_data.VARIABLES[query["variable"]][1], query["origin"].isoformat(), result["time"], query["horizon"],
                             result["value"], result["baseline"], result["observed_after"], result["absolute_error"], result["training_end"],
                             result["source_url"], result["source_sha256"]])
        return response
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except (OSError, KeyError, IndexError):
        logger.exception("No se pudo exportar la consulta histórica")
        return JsonResponse({"error": "La descarga no está disponible en este momento."}, status=503)
