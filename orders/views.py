import json

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from orders.models import OrganizationalUnit
from orders.utils import publish_order

METHODS = ["Completed Order", "Return"]

SAS = "sv=2022-11-02&ss=b&srt=sco&sp=rl&se=2024-11-22T22:07:49Z&st=2023-11-22T14:07:49Z&spr=https&sig=o%2F8MVE7cL5GHN9QJEY4Lb%2F%2FvpbDu56VO1jlMY1JJcF8%3D"


def homepage(request):
    """
    Handles requests to the homepage and returns a simple JSON response.

    Args:
        request (HttpRequest): The incoming request object.

    Returns:
        JsonResponse: A JSON response indicating the service status.
    """
    return JsonResponse({"status": "ok"})


def map(request):
    """
    Renders the 'map.html' template.

    Args:
        request (HttpRequest): The incoming request object.

    Returns:
        HttpResponse: The rendered map template.
    """
    return render(request, "map.html", {})


@csrf_exempt
def ingest(request):
    """
    Ingests organization unit data from an incoming request.

    This view receives a JSON payload that contains a URL pointing to a blob file.
    The file is retrieved, its JSON content is processed to extract organization
    unit details, and the corresponding organization unit is retrieved from the database.
    If the organization unit exists, it publishes the order information using Redis.

    Args:
        request (HttpRequest): The incoming request object, expected to contain a JSON body
                               with the blob URL.

    Returns:
        JsonResponse: A JSON response indicating the result of the operation
                      (either "ok" or "niet ok" in case of an error).
    """

    payload = json.loads(request.body)[0]

    if "validationCode" in payload.get("data"):
        print(payload.get("data").get("validationUrl"))
        requests.get(payload.get("data").get("validationUrl"), allow_redirects=True)
        return JsonResponse({"status": "ok"})

    blob_location = json.loads(request.body)[0].get("data").get("url") + "?" + SAS
    file_response = requests.get(blob_location, allow_redirects=True)
    try:
        payload = file_response.json()
        organization_unit_id = payload["OriginatingOrganizationUnit"].get("ID")
        stored_unit = OrganizationalUnit.objects.filter(gl_id=organization_unit_id)[0]
        publish_order(stored_unit)

    except:
        return JsonResponse({"status": "niet ok"})

    return JsonResponse({"status": "ok"})
