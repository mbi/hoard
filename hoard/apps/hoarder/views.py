import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Category


@require_http_methods(["POST"])
@csrf_exempt
def record(request, slug):
    category = get_object_or_404(Category, slug=slug)
    for h in category.headers.all():
        if request.headers.get(h.key) != h.value:
            return HttpResponseBadRequest("Invalid header value")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid payload")

    hoard = category.hoards.create(data=category.preprocess(payload))
    return JsonResponse({"id": str(hoard.id)})
