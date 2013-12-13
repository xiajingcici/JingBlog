import cgi
import urllib
import webapp2
import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import ndb
from google.appengine.api import users

class Blog(ndb.Model):  
  #blog_id = ndb.IntegerProperty() #seems don't need, GAE will create a unique key id every time you insert a new row
  blogname = ndb.StringProperty()
  blog_url = ndb.StringProperty()
  owner = ndb.UserProperty()
  createtime = ndb.DateTimeProperty(auto_now_add=True)

class MyUtil():
  def renderLogin(self,uri):
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(uri) 
      greeting = 'Welcome Back, '+user.nickname()   
      url_linktext = 'Sign out' 
    else:
      url = users.create_login_url(uri)
      greeting = ""
      url_linktext = 'Sign in or Register'
    template_values = {
      'url': url,
      'greeting': greeting,
      'url_linktext': url_linktext
    }
    return template_values
  def renderAlert(self,alertmessage):
    template = jinja_environment.get_template('templete/innertmp/alert.html')
    template_values = {
       'notice_area': template.render({'message':alertmessage})
    }
    return template_values
  def renderSuccess(self,alertmessage):
    template = jinja_environment.get_template('templete/innertmp/success.html')
    template_values = {
       'notice_area': template.render({'message':alertmessage})
    }
    return template_values
  def renderInfo(self,alertmessage):
    template = jinja_environment.get_template('templete/innertmp/info.html')
    template_values = {
       'notice_area': template.render({'message':alertmessage})
    }
    return template_values
  def renderWarning(self,alertmessage):
    template = jinja_environment.get_template('templete/innertmp/warning.html')
    template_values = {
       'notice_area': template.render({'message':alertmessage})
    }
    return template_values
  
class MainPage(webapp2.RequestHandler):
  def get(self):
    template_values={}
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/temp.html')
    self.response.out.write(template.render(template_values))
 
class AddBlog(webapp2.RequestHandler):
  def get(self):    
    template_values={}
    template_values.update(MyUtil().renderLogin(self.request.uri))     
    template = jinja_environment.get_template('templete/addblog.html')
    self.response.out.write(template.render(template_values))
  def post(self):
    template_values={}
    blog_name = self.request.get('inputBlogName')
    blog_url = self.request.get('inputBlogUrl')
    user = users.get_current_user()
    qry = Blog.query(Blog.blog_url == blog_url)
    if qry.count()==0:
       if user:
         blog = Blog(blogname = blog_name,blog_url = blog_url,owner = user)
         blog.put()
         template_values.update(MyUtil().renderSuccess("Your Blog Created Successful. Enjoy Blogging!"))
       else:
         template_values.update(MyUtil().renderAlert("User service error. Please login again."))
    else:
      template_values.update(MyUtil().renderAlert("This Url is being used by someone else. Please pick another one."))
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/addblog.html')
    self.response.out.write(template.render(template_values))

class ManageBlog(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    if blogs.count()>0:
       template_values={'blogs':blogs}
    else:
       template_values={}
    template_values.update(MyUtil().renderLogin(self.request.uri))
    alert = self.request.get('alert')
    if alert:
       template_values.update(MyUtil().renderAlert(alert))
    success = self.request.get('success')
    if success:
       template_values.update(MyUtil().renderSuccess(success))
    template = jinja_environment.get_template('templete/manageblog.html')
    self.response.out.write(template.render(template_values))

class DeleteBlog(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    id = self.request.get('id')
    if id:
      blog = ndb.Key(Blog, int(id)).get()
      if blog.owner !=user:
        self.redirect("/manageblog?alert=You cannot delete other's blog.")
      else:
        blog.key.delete()
        self.redirect("/manageblog?success=Deleted.")
    else:
      self.redirect("/manageblog?alert=Delete Error. Please try again.")

class EditBlog(webapp2.RequestHandler):
  def get(self):
    self.redirect("/manageblog")

class ViewBlog(webapp2.RequestHandler):
  def get(self):
    self.redirect("/manageblog")

app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/addblog', AddBlog),
  ('/manageblog', ManageBlog),
  ('/deleteblog', DeleteBlog),
  ('/editblog', EditBlog),
  ('/viewblog', ViewBlog)
])
