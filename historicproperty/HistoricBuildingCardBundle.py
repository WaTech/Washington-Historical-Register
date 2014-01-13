import os
import jinja2

__author__ = 'justinb'


class HistoricBuildingCardBundle(object):
    """ Renders a collection of HTML cards about a building """

    _image_uri_base = "https://dl.dropboxusercontent.com/u/6782837/register/"
    jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/../"))
    _title_image_uri = "http://www.k12.wa.us/aboutus/images/StalwartStone1.gif"
    _data = None

    bundle = []

    def __init__(self, data):
        self._data = data
        self.bundle = []

    def _image_uri(self):
        return self._image_uri_base + "%s-01_%s.jpg" % (self._data["Register_I"], self._data["REGISTER_N"].replace(" ", ""))

    def execute(self):
        self.bundle.append(self._get_title_card_body())
        self.bundle.append(self._get_info_card_body())
        return self


    def _get_common_body(self):
        return {
            "notification": {"level": "DEFAULT"},
            "bundleId": self._data["REGISTER_N"],
            "menuItems": [
                {
                    "action": "CUSTOM",
                    "id": self._data["REGISTER_N"],
                    "values": [{
                                   "displayName": "Delete Bundle",
                                   "iconUrl": "http://cdn.mactrast.com/wp-content/uploads/2013/12/GoogleGlassLogo-50x50.png"
                               }]
                }
            ]
        }

    def _get_title_card_body(self):
        title_card_properties = {
            "html": self.jinja_environment.get_template('templates/cards/RegisterInfoTitleCard.html').render({
                "Name": self._data["REGISTER_N"],
                "ImageURI": self._image_uri(),

            }),
            "isBundleCover": "true",
        }
        return dict(self._get_common_body().items() + title_card_properties.items())

    def _get_info_card_body(self):
        info_card_properties = {
            "html": self.jinja_environment.get_template('templates/cards/RegisterInfoCard.html').render({
                "Name":         self._data["REGISTER_N"],
                "Style":        self._data["STYLE_TYPE"],
                "Architect":    self._data["ARCHITECT"],
            })
        }

        return dict(self._get_common_body().items() + info_card_properties.items())