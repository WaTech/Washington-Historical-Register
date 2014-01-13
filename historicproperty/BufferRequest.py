import requests


class BufferRequest():
    """ Calls ESRI geometry server with loc and range, gets back a circular buffer of points. """

    url = "https://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/buffer"
    template = "json/BufferRequestData.json"

    _lat = 0
    _lng = 0
    _dist = 0

    def __init__(self, *args, **kwargs): #, lat, lng, dist):
        self._lat = kwargs["lat"]
        self._lng = kwargs["lng"]
        self._dist = kwargs["dist"]

    def execute(self):
        data = {
            "f":            "json",
            "bufferSR":     "4326",
            "distances":    self._dist or "0.1",
            "inSR":         "4326",
            "unionResults": "false",
            "unit":         "9036",
            "geometries":   '{ "geometryType": "esriGeometryPoint", "geometries": [{"x": %s, "y": %s}] }' % (self._lat, self._lng)
        }

        buffer_response = requests.post(self.url, data=data, timeout=300)
        return buffer_response.json()