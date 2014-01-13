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

"""Request Handler for /notify endpoint."""
from urlparse import urlparse
from google.appengine.api.urlfetch import POST

__author__ = 'justinb@ofm.wa.gov (Justin Burns)'


import os
import json
import logging
import webapp2
from google.appengine.api import urlfetch

from oauth2client.appengine import StorageByKeyName
from google.appengine.api import taskqueue
from model import Credentials
import util

DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')

class NotifyHandler(webapp2.RequestHandler):
  """Request Handler for notification pings."""

  def post(self):
    """Handles notification pings."""
    logging.info('Got a notification with payload %s', self.request.body)
    data = json.loads(self.request.body)


    self.userid = data['userToken'] # TODO: Check that the userToken is a valid userToken.

    self.mirror_service = util.create_service('mirror', 'v1',
        StorageByKeyName(Credentials, self.userid, 'credentials').get())

    if data.get('collection') == 'locations':
      self._handle_locations_notification(data)
    elif data.get('collection') == 'timeline':
      self._handle_timeline_notification(data)


  def _handle_locations_notification(self, data):
    location = self.mirror_service.locations().get(id=data['itemId']).execute()
    lat = location.get('latitude')
    lng = location.get('longitude')

    data = {U'location': location, u'latitude': lat, u'longitude': lng, u'dist': 1, u'userToken': self.userid}

    parsed_url = urlparse(self.request.url)
    url = '%s://%s/historicproperty' % (parsed_url.scheme, parsed_url.netloc)

    if DEV:
      try:
        rpc = urlfetch.create_rpc(deadline=1)
        urlfetch.make_fetch_call(rpc, url, method=POST, payload=json.dumps(data), follow_redirects=True) #headers=my_headers,
        rpc_result = rpc.get_result()
      except:
        print("Deadline timed out...")
    else:
      taskqueue.add(url="/historicproperty", payload=json.dumps(data))


  def _handle_timeline_notification(self, data):
    """Handle timeline notification."""

    for user_action in data.get('userActions', []):
      # Fetch the timeline item.
      item = self.mirror_service.timeline().get(id=data['itemId']).execute()


      if user_action.get('type') == 'SHARE':
        # Create a dictionary with just the attributes that we want to patch.
        body = { 'text': 'Washington Historical Register got your photo! %s' % item.get('text', '') }

        # Patch the item. Notice that since we retrieved the entire item above
        # in order to access the caption, we could have just changed the text
        # in place and used the update method, but we wanted to illustrate the
        # patch method here.
        self.mirror_service.timeline().patch(id=data['itemId'], body=body).execute()

        # Only handle the first successful action.
        break

      # elif user_action.get('type') == 'NAVIGATE':
      #     pass

      # elif user_action.get('type') == 'CUSTOM':
      #   logging.info("Deleting id #" % data['itemId'])

      # elif user_action.get('type') == 'LAUNCH':
      #   # Grab the spoken text from the timeline card and update the card with
      #   # an HTML response (deleting the text as well).
      #   note_text = item.get('text', '');
      #   utterance = choice(CAT_UTTERANCES)
      #
      #   item['text'] = None
      #   item['html'] = ("<article class='auto-paginate'>" +
      #       "<p class='text-auto-size'>" +
      #       "Oh, did you say " + note_text + "? " + utterance + "</p>" +
      #       "<footer><p>Python Quick Start</p></footer></article>")
      #   item['menuItems'] = [{ 'action': 'DELETE' }];
      #
      #   self.mirror_service.timeline().update(id=item['id'], body=item).execute()

      else:
        logging.info("I don't know what to do with this notification: %s", user_action)


NOTIFY_ROUTES = [
    ('/notify', NotifyHandler)
]
