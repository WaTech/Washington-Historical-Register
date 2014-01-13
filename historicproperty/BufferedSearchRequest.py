import json
import requests
from historicproperty.BufferRequest import BufferRequest


class BufferedSearchRequest():
    """ Queries an ESRI map layer for all points that fall within our buffer """
    url = "http://services.arcgis.com/jsIt88o09Q0r1j8h/ArcGIS/rest/services/Historic_Downtown_Olympia_Register_Buildings/FeatureServer/0/query"

    template = 'json/BufferedQueryRequestData.json'

    _buffer = None

    def __init__(self, *args, **kwargs): #, lat, lng, dist):
        self._lat = kwargs["lat"]
        self._lng = kwargs["lng"]
        self._dist = kwargs["dist"]

    def execute(self):
        """ Uses lat/lng/dist values to create a circular buffer, then searches for properties inside the buffer """
        buffer_result = BufferRequest(lat=self._lat, lng=self._lng, dist=self._dist).execute()
        buffer_geometry = buffer_result["geometries"][0]

        data = {
            "f":                "json",
            "geometryType":     "esriGeometryPolygon",
            "inSR":             "4326",
            "outFields":        "*",
            "outSR":            "4326",
            "returnGeometry":   "true",
            "spatialRel":       "esriSpatialRelIntersects",
            "geometry":         json.dumps(buffer_geometry)
        }

        buffered_search_response = requests.post(self.url, data=data, timeout=300)
        return buffered_search_response.json()