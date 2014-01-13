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

"""Datastore models for Starter Project"""
from datetime import datetime

__author__ = 'justinb@ofm.wa.gov (Justin Burns)'


from google.appengine.ext import db

from oauth2client.appengine import CredentialsProperty

class OCIOGlassUser(db.Model):
  user_id = db.StringProperty(required=True)
  last_accessed = db.DateTimeProperty()

class HistoricalSite(db.Model):
    site = db.StringProperty(required=True)
    is_active = db.BooleanProperty(default=False)
    last_seen = db.DateTimeProperty(default=datetime.now())

class Credentials(db.Model):
  """Datastore entity for storing OAuth2.0 credentials.

  The CredentialsProperty is provided by the Google API Python Client, and is
  used by the Storage classes to store OAuth 2.0 credentials in the data store.
  """
  credentials = CredentialsProperty()
