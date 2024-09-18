import json
import os
import time

import redis
import requests
from azure.storage.blob import BlobServiceClient
from azure.storage.filedatalake import DataLakeServiceClient
from django.conf import settings

from orders.models import OrganizationalUnit

##TODO: Clean up this cesspool of variables.

REDIS_URL = settings.REDIS_HOST
REDIS_CONNECTION_POOL = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

EVA_ENDPOINT = "https://api.euw.newblack.test.eva-online.cloud/"
AGENT = "insights"
API_KEY = "Token 04E2BB04F6D7EC1A5846E8DEA7428E5421404D00BE3C3A2126C81E478D4348DB"
LIST_DATA = {"PageConfig": {"SortDirection": 0, "Limit": 300}}

HEADERS = {
    "Authorization": "Token 04E2BB04F6D7EC1A5846E8DEA7428E5421404D00BE3C3A2126C81E478D4348DB",
    "EVA-User-Agent": "app",
}

LIST_OUS_ENDPOINTS = [
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/ase-prod-rituals.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/cus-prod-guc-newblack.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-ajax.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-dyson.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-fenix.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-grandvision-pt.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-gstar.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-kiko.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-rituals.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/euw-prod-scotch-2021.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/gwc-prod-ide.json",
    "https://nbinsights.dfs.core.windows.net/eva-insights/production/organizationunits/2024/08/27/gwc-prod-intersport.json",
]

SAS_TOKEN = "sv=2022-11-02&ss=b&srt=sco&sp=rl&se=2024-11-22T22:07:49Z&st=2023-11-22T14:07:49Z&spr=https&sig=o%2F8MVE7cL5GHN9QJEY4Lb%2F%2FvpbDu56VO1jlMY1JJcF8%3D"

ACCOUNT_URL = "https://nbinsights.blob.core.windows.net/"
DB_NAME = "EVA"
FOLDER_PREFIX = "/production/organizationunits/2024/08/27/"
CONTAINER = "eva-insights"


CHANNEL = "orders"


def connect(redis_url):
    """
    Establishes a connection to a Redis server using the provided URL.

    If a Redis connection already exists through the REDIS_CONNECTION_POOL, it returns that connection.
    Otherwise, it tries to connect repeatedly until a successful connection is made.

    Args:
        redis_url (str): The URL of the Redis server to connect to.

    Returns:
        Redis: A Redis connection object.
    """
    if redis.Redis(connection_pool=REDIS_CONNECTION_POOL):
        return redis.Redis(connection_pool=REDIS_CONNECTION_POOL)

    while True:
        print('Trying to connect to redis at "%s" ...' % redis_url)
        try:
            connection = redis.StrictRedis.from_url(redis_url, decode_responses=True)
            connection.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError):
            time.sleep(1)
        else:
            break
    print('Connected to redis at "%s".' % redis_url)
    return connection


def get_redis_connection():
    """
    Retrieves or creates a Redis connection from the REDIS_CONNECTION_POOL.

    If the connection pool is valid, it returns a Redis instance using the pool.

    Returns:
        Redis: A Redis connection object.
    """
    return redis.Redis(connection_pool=REDIS_CONNECTION_POOL)


def trace(*args):
    """
    Prints the provided arguments in a formatted, optionally colorized string.

    Args:
        *args: Any number of arguments to print.

    Returns:
        None
    """
    colorize = True
    text = ""
    if colorize:
        text += "\x1b[1;33;40m"
    text += ", ".join([str(arg) for arg in args])
    if colorize:
        text += "\x1b[0m"
    print(text)


def get_organizational_units_summaries():
    """
    Fetches organizational unit summaries from a remote API and updates or creates
    OrganizationalUnit objects with the retrieved data.

    Makes a POST request to the EVA_ENDPOINT API, parses the response, and processes the data
    to either create or update OrganizationalUnit instances in the database.

    Returns:
        Response: The response object from the API request.
    """
    data = json.dumps(LIST_DATA)

    response = requests.post(
        "{}{}".format(EVA_ENDPOINT, "message/ListOrganizationUnitSummaries"),
        data=data,
        headers=HEADERS,
    )

    json_response = response.json()

    nm_pages = json_response["Result"]["NumberOfPages"]
    nm_ous_pp = len(json_response["Result"]["Page"])
    page = json_response["Result"]["Page"]

    for ix in range(nm_pages):
        print(ix)

    for ix in range(nm_ous_pp):
        if "Address" in page[ix]:

            if "Latitude" in page[ix]["Address"].keys():
                latitude = page[ix]["Address"]["Latitude"]
                longitude = page[ix]["Address"]["Longitude"]
            elif "Latitude" in page[ix]:
                latitude = page[ix]["Latitude"]
                longitude = page[ix]["Longitude"]
            else:
                latitude = longitude = None

            OrganizationalUnit.objects.get_or_create(
                ou_id=page[ix].get("ID", "NA"),
                add_id=page[ix].get("Address", "NA").get("ID", "NA"),
                name=page[ix].get("Name", "NA"),
                address=page[ix].get("Address", "NA").get("Address1", "NA"),
                house_number=page[ix].get("Address", "NA").get("HouseNumber", "NA"),
                city=page[ix].get("Address", "NA").get("City", "NA"),
                post_code=page[ix].get("Address", "NA").get("ZipCode", "NA"),
                country=page[ix].get("Address", "NA").get("CountryID", "NA"),
                latitude=latitude,
                longitude=longitude,
            )
        print(ix)

    return response


def get_service_client_sas(account_name: str, sas_token: str) -> DataLakeServiceClient:
    """
    Returns a DataLakeServiceClient instance using a storage account name and a SAS token.

    Args:
        account_name (str): The name of the Azure Storage account.
        sas_token (str): The Shared Access Signature (SAS) token for authentication.

    Returns:
        DataLakeServiceClient: The service client for interacting with Azure Data Lake.
    """
    account_url = f"https://{account_name}.dfs.core.windows.net"

    # The SAS token string can be passed in as credential param or appended to the account URL
    service_client = DataLakeServiceClient(account_url, credential=sas_token)

    return service_client


def read_organization_details():
    """
    Reads organizational details from blobs stored in an Azure Blob container.

    For each endpoint in LIST_OUS_ENDPOINTS, retrieves the blob data from the container, parses
    the JSON, and creates or updates OrganizationalUnit objects.

    Returns:
        None
    """
    container_client = BlobServiceClient(
        account_url=ACCOUNT_URL, credential=SAS_TOKEN
    ).get_container_client(CONTAINER)

    for ou_export in LIST_OUS_ENDPOINTS:
        client_name = ou_export.split("/")[-1].split("-")[-1][:-4]
        all_ous = container_client.list_blobs(FOLDER_PREFIX)

        for blob in all_ous:
            blob_client = container_client.get_blob_client(blob.name)
            data = json.loads(blob_client.download_blob().readall())

            blob_contents = data.get("OrganizationUnits")

            for ou in blob_contents:

                if "Latitude" in ou:
                    latitude = ou["Latitude"]
                    longitude = ou["Longitude"]
                else:
                    latitude = longitude = 0.0

                ou_id = ou.get("ID")

                print("{}: {}".format(client_name, ou_id))

                if ou_id:

                    try:
                        if "Address" in ou.keys():
                            OrganizationalUnit.objects.get_or_create(
                                gl_id=ou.get("ID"),
                                name=ou.get("Name", "NA"),
                                client_name=client_name,
                                address=ou.get("Address", "NA").get("Address1", "NA"),
                                house_number=ou.get("Address", "NA").get(
                                    "HouseNumber", "NA"
                                ),
                                city=ou.get("Address", "NA").get("City", "NA"),
                                post_code=ou.get("Address", "NA").get("ZipCode", "NA"),
                                country=ou.get("Address", "NA").get("CountryID", "NA"),
                                latitude=latitude,
                                longitude=longitude,
                            )
                        else:
                            OrganizationalUnit.objects.get_or_create(
                                gl_id=ou.get("ID"),
                                latitude=latitude,
                                longitude=longitude,
                            )
                    except:
                        print("Exception for: {}".format(blob))


def publish_order(organizational_unit):
    """
    Publishes organizational unit data to a Redis channel.

    Retrieves a Redis connection using the `connect` function, converts the organizational
    unit data to coordinates, and publishes it to a Redis channel.

    Args:
        organizational_unit: An instance of the OrganizationalUnit model.

    Returns:
        int: Always returns 0.
    """
    connection = connect(REDIS_URL)

    data = organizational_unit.to_coords()

    connection.publish(CHANNEL, data)

    return 0
