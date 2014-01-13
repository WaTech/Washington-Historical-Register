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

"""Request Handler for /main endpoint."""
import json
from google.appengine.api.urlfetch import POST
from OCIORequestHandler import OCIORequestHandler

__author__ = 'justinb@ofm.wa.gov (Justin Burns)'

import io
import logging
import os
import util

from pprint import pprint
from urlparse import urlparse

import jinja2

from apiclient import errors
from apiclient.http import MediaIoBaseUpload
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from google.appengine.api.labs import taskqueue

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')
if not DEV:
    from google.appengine.api import background_thread


class MainHandler(OCIORequestHandler):
    """Request Handler for the main endpoint."""

    def _render_template(self, message=None):
        """Render the main page template."""
        template_values = {'userId': self.userid}
        if message:
            template_values['message'] = message
            # self.mirror_service is initialized in util.auth_required.
        try:
            template_values['contact'] = self.mirror_service.contacts().get(
                id='washington-historic-register').execute()
        except errors.HttpError:
            logging.info('Unable to find Historic Register contact.')

        timeline_items = self.mirror_service.timeline().list(maxResults=3).execute()
        template_values['timelineItems'] = timeline_items.get('items', [])

        subscriptions = self.mirror_service.subscriptions().list().execute()

        for subscription in subscriptions.get('items', []):
            collection = subscription.get('collection')

            if collection == 'timeline':
                template_values['timelineSubscriptionExists'] = True
            elif collection == 'locations':
                template_values['locationSubscriptionExists'] = True

        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render(template_values))

    @util.auth_required
    def get(self):
        """Render the main page."""
        # Get the flash message and delete it.
        message = memcache.get(key=self.userid)
        memcache.delete(key=self.userid)
        self._render_template(message)

    @util.auth_required
    def post(self):
        """Execute the request and render the template."""

        operation = self.request.get('operation')

        # Dict of operations to easily map keys to methods.
        operations = {
            'insertSubscription': self._insert_subscription,
            'deleteSubscription': self._delete_subscription,

            'insertContact': self._insert_contact,
            'deleteContact': self._delete_contact,

            'deleteTimelineItem': self._delete_timeline_item,
            'propertiesForLocation': self._insert_properties_for_location,

            'clearTimeline': self._clear_timeline,
        }

        if operation in operations:
            message = operations[operation]()
        else:
            message = "I don't know how to " + operation

        # Store the flash message for 5 seconds.
        memcache.set(key=self.userid, value=message, time=5)

        self.redirect('/')


    def _clear_timeline(self):
        for card in self.mirror_service.timeline().list().execute().items():
            self.mirror_service.contacts().delete(id=card.get("id")).execute()

    def _insert_subscription(self):
        """Subscribe the app."""
        body = {
            'collection': self.request.get('collection', 'timeline'),
            'userToken': self.userid,
            'callbackUrl': util.get_full_url(self, '/notify')
        }

        # self.mirror_service is initialized in util.auth_required.
        self.mirror_service.subscriptions().insert(body=body).execute()
        return 'Application is now subscribed to updates.'


    def _delete_subscription(self):
        """Unsubscribe from notifications."""
        collection = self.request.get('subscriptionId')
        self.mirror_service.subscriptions().delete(id=collection).execute()
        return 'Application has been unsubscribed.'


    def _insert_properties_for_location(self):
        params = self.request.params
        parsed_url = urlparse(self.request.url)

        url = '%s://%s/historicproperty' % (parsed_url.scheme, parsed_url.netloc)

        data = {u'latitude': params["latitude"], u'longitude': params["longitude"], u'dist': params["dist"],
                u'userToken': self.userid}

        if DEV:
            try:
                rpc = urlfetch.create_rpc(deadline=1)
                urlfetch.make_fetch_call(rpc, url, method=POST, payload=json.dumps(data),
                                         follow_redirects=True) #headers=my_headers,
                rpc.get_result()
            except:
                print("Deadline timed out...")

        else:
            taskqueue.add(url="/historicproperty", payload=json.dumps(data))

        return "Message received, captain!"

    def _insert_contact(self):
        """Insert a new Contact."""
        logging.info('Inserting contact')
        id = self.request.get('id')
        name = self.request.get('name')
        image_url = self.request.get('imageUrl')

        if not name or not image_url:
            return 'Must specify imageUrl and name to insert contact'
        else:
            if image_url.startswith('/'):
                image_url = util.get_full_url(self, image_url)

            body = {
                'id': id,
                'displayName': name,
                'imageUrls': [image_url],
                'acceptCommands': [{'type': 'TAKE_A_NOTE'}]
            }

            self.mirror_service.contacts().insert(body=body).execute()
            return 'Inserted contact: ' + name

    def _delete_contact(self):
        """Delete a Contact."""
        self.mirror_service.contacts().delete(id=self.request.get('id')).execute()
        return 'Contact has been deleted.'

    def _delete_timeline_item(self):
        """Delete a Timeline Item."""
        logging.info('Deleting timeline item')
        # self.mirror_service is initialized in util.auth_required.
        self.mirror_service.timeline().delete(id=self.request.get('itemId')).execute()
        return 'A timeline item has been deleted.'


MAIN_ROUTES = [
    ('/', MainHandler)
]