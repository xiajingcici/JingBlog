import cgi
import urllib
import webapp2
import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import ndb
from google.appengine.api import users

class MainPage(webapp2.RequestHandler):
  def get(self):    
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(self.request.uri)	
      greeting = 'Welcome Back, '+user.nickname()	  
      url_linktext = 'Sign out' 
    else:
      url = users.create_login_url(self.request.uri)
      greeting = ""
      url_linktext = 'Sign in or register'

    template_values = {      
      'url': url,
      'greeting': greeting,
      'url_linktext': url_linktext
    }

    template = jinja_environment.get_template('templete/temp.html')
    self.response.out.write(template.render(template_values))	
	
app = webapp2.WSGIApplication([
  ('/', MainPage)
])
