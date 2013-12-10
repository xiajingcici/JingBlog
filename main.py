import cgi
import urllib
import webapp2
import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import ndb
from google.appengine.api import users

class Greeting(ndb.Model):
  """Models an individual guestbook entry with author, content, and date."""
  author = ndb.UserProperty()
  content = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def query_book(cls, ancestor_key):
    return cls.query(ancestor=ancestor_key).order(-cls.date)

class MainPage(webapp2.RequestHandler):
  def get(self):
    guestbook_name = self.request.get('guestbook_name')
    # There is no need to actually create the parent Book entity; we can
    # set it to be the parent of another entity without explicitly creating it
    ancestor_key = ndb.Key("Book", guestbook_name or "*notitle*")
    greetings = Greeting.query_book(ancestor_key).fetch(20)

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'greetings': greetings,
      'url': url,
      'url_linktext': url_linktext,
      'guestbook_name': guestbook_name

    }

    template = jinja_environment.get_template('templete/temp.html')
    self.response.out.write(template.render(template_values))	
	
class Guestbook(webapp2.RequestHandler):
  def post(self):
    # Set parent key on each greeting to ensure that each
    # guestbook's greetings are in the same entity group.
    guestbook_name = self.request.get('guestbook_name')
    # There is no need to actually create the parent Book entity; we can
    # set it to be the parent of another entity without explicitly creating it
    greeting = Greeting(parent=ndb.Key("Book", guestbook_name or "*notitle*"),
                        content = self.request.get('content'))
    if users.get_current_user():
      greeting.author = users.get_current_user()
    greeting.put()
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))

app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/sign', Guestbook)
])
