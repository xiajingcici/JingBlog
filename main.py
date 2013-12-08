import cgi
import urllib
import webapp2

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
    self.response.out.write('<html><body>')
    guestbook_name = self.request.get('guestbook_name')
    # There is no need to actually create the parent Book entity; we can
    # set it to be the parent of another entity without explicitly creating it
    ancestor_key = ndb.Key("Book", guestbook_name or "*notitle*")
    greetings = Greeting.query_book(ancestor_key).fetch(20)

    for greeting in greetings:
      if greeting.author:
        self.response.out.write(
            '<b>%s</b> wrote:' % greeting.author.nickname())
      else:
        self.response.out.write('An anonymous person wrote:')
      self.response.out.write('<blockquote>%s</blockquote>' %
                              cgi.escape(greeting.content))

    self.response.out.write("""
          <form action="/sign" method="post">
            <input type="hidden" value="%s" name="guestbook_name">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
          <hr>
          <form>Guestbook name: <input value="%s" name="guestbook_name">
          <input type="submit" value="switch"></form>
        </body>
      </html>""" % (cgi.escape(guestbook_name), cgi.escape(guestbook_name)))

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
