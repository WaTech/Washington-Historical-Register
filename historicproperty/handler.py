# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'justinb@ofm.wa.gov (Justin Burns)'

from historicproperty.BufferRequest import BufferRequest
from historicproperty.BufferedSearchRequest import BufferedSearchRequest

import webapp2
import jinja2
import json
import os
import util
import logging

from oauth2client.appengine import StorageByKeyName
from model import Credentials, HistoricalSite
from apiclient.discovery import build
from datetime import datetime, timedelta

from HistoricBuildingCardBundle import HistoricBuildingCardBundle

task_api = build('taskqueue', 'v1beta2')

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/../"))

class HistoricPropertyHandler(webapp2.RequestHandler):
  """Request Handler for the Historic Properties endpoint."""

  def post(self):
    myparams = json.loads(self.request.body)

    ocio_user = util.get_ocio_user(myparams['userToken'])
    mirror_service = util.create_service('mirror', 'v1', StorageByKeyName(Credentials, ocio_user.user_id, 'credentials').get())

    # Return buildings that fall within the buffer zone
    buffered_query_result = BufferedSearchRequest(lat=myparams["latitude"], lng=myparams["longitude"], dist=myparams["dist"]).execute()


    for feature in buffered_query_result["features"]:
        record = feature["attributes"]

        if record is None or "REGISTER_N" not in record or record["REGISTER_N"] == "":
            continue

        # Get site object from datastore, to determine see if we've already seen this card
        site = HistoricalSite.get_by_key_name(record["REGISTER_N"], parent=ocio_user)

        if not hasattr(site, "site"):
            logging.info("%s has no record, inserting one!" % record["REGISTER_N"])
            newsite = HistoricalSite(key_name=record["REGISTER_N"],
                                     site=record["REGISTER_N"],
                                     parent=ocio_user,
                                     is_active=True,
                                     last_seen=datetime.now())
            newsite.put()
            for card in HistoricBuildingCardBundle(record).execute().bundle:
                    mirror_service.timeline().insert(body=card).execute()

        elif site.is_active:
            logging.info("%s is already active, not inserting" % record["REGISTER_N"])
            site.last_seen = datetime.now()
            site.put()

        elif datetime.now() - site.last_seen > timedelta(hours=1):
            logging.info("%s is inactive, and enough time has passed. Add it again." % record["REGISTER_N"])
            site.is_active = True
            site.last_seen = datetime.now()
            site.put()

            for card in HistoricBuildingCardBundle(record).execute().bundle:
                mirror_service.timeline().insert(body=card).execute()

HISTORIC_PROPERTY_ROUTES = [
    ('/historicproperty', HistoricPropertyHandler)
]