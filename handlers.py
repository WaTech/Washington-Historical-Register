from google.appengine.ext import webapp
from google.appengine.api import mail

class YourMail(webapp.RequestHandler):

  def post(self):
    body_string = self.request.get("body_string")
    mail.send_mail(
      sender="you@your-domain.appengine.com",
      to="abc@abc.com",
      subject="Your subject",
      body=body_string)