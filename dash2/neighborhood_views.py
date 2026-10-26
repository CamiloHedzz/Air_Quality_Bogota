"""Descargas locales reproducibles del dataset exploratorio del mapa."""
from django.http import FileResponse, JsonResponse, HttpResponseNotModified
from django.views.decorators.http import require_GET
from . import neighborhood_data


@require_GET
def methodology(request):
    path=neighborhood_data.ROOT/'notebooks/05_integracion_historica_2015_2025.ipynb'
    return FileResponse(path.open('rb'),as_attachment=True,filename=path.name,content_type='application/x-ipynb+json')


@require_GET
def calendar(request):
    neighborhood_data.load_history()
    path=neighborhood_data.ROOT/'data/maps/station_daily_2015_2025.csv.gz'
    return FileResponse(path.open('rb'),as_attachment=True,filename=path.name,content_type='application/gzip')


@require_GET
def manifest(request):
    return JsonResponse(neighborhood_data.load_history()[2],json_dumps_params={'ensure_ascii':False,'allow_nan':False})


@require_GET
def geometry(request):
    metadata = neighborhood_data.load_history()[2]
    digest = metadata['input_sha256']['dash2/datasets/bogota_cadastral.json']
    etag = f'"{digest}"'
    if request.headers.get('If-None-Match') == etag:
        response = HttpResponseNotModified()
    else:
        path = neighborhood_data.ROOT/'dash2/datasets/bogota_cadastral.json'
        response = FileResponse(path.open('rb'), content_type='application/geo+json')
    response['ETag'] = etag
    response['Cache-Control'] = 'public, max-age=31536000, immutable' if request.GET.get('v') == digest[:16] else 'no-cache'
    return response
