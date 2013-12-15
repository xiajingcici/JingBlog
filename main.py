import cgi
import urllib
import webapp2
import jinja2
import os
import re
import datetime


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search

#https://developers.google.com/appengine/docs/python/mail/receivingmail   Handling Incoming Email

class Blog(ndb.Model):  
  #blog_id = ndb.IntegerProperty() #seems don't need, GAE will create a unique key id every time you insert a new row
  blogname = ndb.StringProperty()
  blog_desc = ndb.StringProperty()
  owner = ndb.UserProperty()
  createtime = ndb.DateTimeProperty(auto_now_add=True)

class Post(ndb.Model):  
  post_title = ndb.StringProperty()
  blog_id = ndb.IntegerProperty()
  owner = ndb.UserProperty()
  publishdatetime = ndb.DateTimeProperty(auto_now_add=True)
  lastmodifydatetime = ndb.DateTimeProperty()
  commentpost = ndb.KeyProperty(kind='Post', repeated=False)
  editor = ndb.UserProperty()
  contents = ndb.StringProperty(repeated=True)
  tags = ndb.StringProperty(repeated=True)
  #https://developers.google.com/appengine/docs/python/ndb/queries#repeated_properties Querying for Repeated Properties
  
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
  def renderContent(self,content):        
    p2 = re.compile(r'(https?://[^\s]+\.jpg|gif|png)',re.I)
    content = p2.sub(r'<img src="\1"/>',content)
    p1 = re.compile(r"[^src=\"](https?://[^\s]+)",re.I)
    content = p1.sub(r'<a href="\1" target="_blank">\1</a>',content)    
    content = content.replace("\n", " <br/>");
    return content;
  def searchText(self,content,keyword):
    return None;
  
class MainPage(webapp2.RequestHandler):
  def get(self):
    template_values={}
    blogs = Blog.query().order(Blog.createtime)
    if blogs.count()>0:
       template_values.update({'blogs':blogs})    
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/index.html')
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
    blog_desc = self.request.get('inputBlogDesc')
    user = users.get_current_user()    
    if user:
        blog = Blog(blogname = blog_name,blog_desc = blog_desc,owner = user)
        blog.put()
        template_values.update(MyUtil().renderSuccess("Your Blog Created Successful. Enjoy Blogging!"))
    else:
        template_values.update(MyUtil().renderAlert("User service error. Please login again."))    
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
      if blog:
        if blog.owner !=user:
          self.redirect("/manageblog?alert=You cannot delete other's blog.")
        else:
          blog.key.delete()
          self.redirect("/manageblog?success=Deleted.")
      else:
        self.redirect("/manageblog?alert=Cannot find this blog.")
    else:
      self.redirect("/manageblog?alert=Delete Error. Please try again.")

class EditBlog(webapp2.RequestHandler):
  def get(self):
    self.redirect("/manageblog")

class ViewBlog(webapp2.RequestHandler):
  def get(self,blog_id):
    blog = ndb.Key(Blog, int(blog_id)).get()    
    if not blog:
        self.redirect("/")
    else:
        template_values={}
        tag = self.request.get('tag')
        if not tag:
            qry =Post.query(Post.blog_id==blog.key.id()).order(-Post.publishdatetime)
        else:
            qry =Post.query(Post.blog_id==blog.key.id(),Post.tags==tag).order(-Post.publishdatetime)
            template_values.update({'tag_filter':tag})
        tags=[]
        for thispost in qry:
            if thispost.tags:
                tags.extend(thispost.tags)
        tags=list(set(tags))
        tags_str=""
        for thistag in tags:
            tags_str = tags_str+'<a href="/viewblog/'+str(blog_id)+'?tag='+thistag+'">'+thistag+"</a>"+", "
        template_values.update({'tags_str':tags_str[:-2]})
        search = self.request.get('search')
        if search:
            qry=Post.query(Post.blog_id==blog.key.id()).order(-Post.publishdatetime)
            posts=[]
            for post in qry:
                thiscontent = "".join(post.contents)
                if MyUtil().searchText(thiscontent,search):
                    posts.append(post)
            qry=posts
        if qry.count(11) > 10:
            posts = qry.fetch(10)
            oldlink = ""
            template_values.update({'blog':blog,'posts':posts,'oldlink':oldlink})
        elif qry.count() == 0:
            template_values.update({'blog':blog})
        else:
            posts = qry
            template_values.update({'blog':blog,'posts':posts})        
        template_values.update(MyUtil().renderLogin(self.request.uri))
        template = jinja_environment.get_template('templete/viewblog.html')
        self.response.out.write(template.render(template_values))

class AddPost(webapp2.RequestHandler):
  def get(self):    
    template_values={}
    user = users.get_current_user()
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    if blogs.count()>0:
       template_values={'blogs':blogs}
    else:
       template_values={}
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/addpost.html')
    self.response.out.write(template.render(template_values))
  def post(self):
    template_values={}
    blog_id = self.request.get('chooseblog')
    post_title = self.request.get('inputPostName')
    post_content = self.request.get('inputPostContent')
    post_tags = self.request.get('inputTags')
    user = users.get_current_user()
    blog = ndb.Key(Blog, int(blog_id)).get()
    oktowrite = None
    if blog:
      if blog.owner !=user:
        template_values.update(MyUtil().renderAlert("You are not authorized to add post in this blog."))
      else:
	    oktowrite = True
    else:
      template_values.update(MyUtil().renderAlert("Cannot find the blog you choose. Please try again."))
    if oktowrite:
      chunks, chunk_size = len(post_content), 500
      content_split = [ post_content[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
      tag_split = [x.strip() for x in post_tags.split(',')]
      post = Post(post_title=post_title,blog_id=int(blog_id),owner=user,contents=content_split,tags=list(set(tag_split)))
      post.put()
      template_values.update(MyUtil().renderSuccess("Your Article Saved Successful. Enjoy Blogging!"))
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    if blogs.count()>0:
       template_values.update({'blogs':blogs})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/addpost.html')
    self.response.out.write(template.render(template_values))
 
class ManagePost(webapp2.RequestHandler):
  def get(self):
    template_values={}
    user = users.get_current_user()
    posts = Post.query(Post.owner==user).order(-Post.publishdatetime)    
    if posts.count()>0:
        template_values.update({'posts':posts})
        blogid_name={}
        for post in posts:
            thisblog=ndb.Key(Blog, post.blog_id).get()
            blogid_name.update({post.blog_id:thisblog.blogname}) 
        template_values.update({'blogid_name':blogid_name})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/managepost.html')
    self.response.out.write(template.render(template_values))

class ViewPost(webapp2.RequestHandler):
  def get(self,post_id):
    template_values={}
    user = users.get_current_user()
    #post_id = self.request.get('id')
    #post_id = id
    if post_id:
        post = ndb.Key(Post, int(post_id)).get()
    else:
        template_values.update(MyUtil().renderAlert("Cannot find post by this id! Please try again later."))
        posts = Post.query(Post.owner==user).order(-Post.publishdatetime)
        if posts.count()>0:
            template_values.update({'posts':posts})
        template_values.update(MyUtil().renderLogin(self.request.uri))    
        template = jinja_environment.get_template('templete/managepost.html')
        self.response.out.write(template.render(template_values))
    blog=ndb.Key(Blog, post.blog_id).get()
    content=""
    for cont in post.contents:
        content=content+cont    
    content = MyUtil().renderContent(content)
    tags=""
    for tag in post.tags:
        tags=tags+'<a href="/viewblog/'+str(post.blog_id)+'?tag='+tag+'">'+tag+"</a>"+", "
    if len(tags)>2:
        template_values.update({'blog':blog,'post':post,'content':content,'tags':tags[:-2]})
    else:
        template_values.update({'blog':blog,'post':post,'content':content,'tags':tags})
    if post.owner == user:
        template_values.update({'hasright':'yes'})
    template_values.update(MyUtil().renderLogin(self.request.uri))    
    template = jinja_environment.get_template('templete/viewpost.html')
    self.response.out.write(template.render(template_values))

class EditPost(webapp2.RequestHandler):
  def get(self,post_id):    
    template_values={}
    user = users.get_current_user()
    #post_id = self.request.get('id')
    if post_id:
        post = ndb.Key(Post, int(post_id)).get()
    else:
        template_values.update(MyUtil().renderAlert("Cannot find post by this id! Please try again later."))
        posts = Post.query(Post.owner==user).order(-Post.publishdatetime)
        if posts.count()>0:
            template_values.update({'posts':posts})
            blogid_name={}
            for post in posts:
                thisblog=ndb.Key(Blog, post.blog_id).get()
                blogid_name.update({post.blog_id:thisblog.blogname}) 
            template_values.update({'blogid_name':blogid_name})            
        template_values.update(MyUtil().renderLogin(self.request.uri))    
        template = jinja_environment.get_template('templete/managepost.html')
        self.response.out.write(template.render(template_values))
    blog=ndb.Key(Blog, post.blog_id).get()
    content=""
    for cont in post.contents:
        content=content+cont    
    tags=""
    for tag in post.tags:
        tags=tags+tag+", "
    if len(tags)>2:
        template_values.update({'blog':blog,'post':post,'content':content,'tags':tags[:-2]})
    else:
        template_values.update({'blog':blog,'post':post,'content':content,'tags':tags})
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    if blogs.count()>0:
       template_values.update({'blogs':blogs})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/editpost.html')
    self.response.out.write(template.render(template_values))
    
class SavePost(webapp2.RequestHandler):    
  def post(self):
    template_values={}
    post_id = self.request.get('post_id')
    blog_id = self.request.get('chooseblog')
    post_title = self.request.get('inputPostName')
    post_content = self.request.get('inputPostContent')
    post_tags = self.request.get('inputTags')
    user = users.get_current_user()
    blog = ndb.Key(Blog, int(blog_id)).get()
    oktowrite = None
    if blog:
      if blog.owner !=user:
        template_values.update(MyUtil().renderAlert("You are not authorized to add post in this blog."))
      else:
	    oktowrite = True
    else:
      template_values.update(MyUtil().renderAlert("Cannot find the blog you choose. Please try again."))
    if oktowrite:
      chunks, chunk_size = len(post_content), 500
      content_split = [ post_content[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
      tag_split = [x.strip() for x in post_tags.split(',')]
      post = ndb.Key(Post, int(post_id)).get()
      post.post_title = post_title
      post.blog_id = int(blog_id)
      post.contents=content_split
      post.tags=list(set(tag_split))
      post.editor=user
      post.lastmodifydatetime = datetime.datetime.now()      
      post.put()
      template_values.update(MyUtil().renderSuccess("Your Article Saved Successful. Enjoy Blogging!"))
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    if blogs.count()>0:
       template_values.update({'blogs':blogs})    
    posts = Post.query(Post.owner==user).order(-Post.publishdatetime)
    if posts.count()>0:
        template_values.update({'posts':posts})
        blogid_name={}
        for post in posts:
            thisblog=ndb.Key(Blog, post.blog_id).get()
            blogid_name.update({post.blog_id:thisblog.blogname}) 
        template_values.update({'blogid_name':blogid_name})              
    template_values.update(MyUtil().renderLogin(self.request.uri))    
    template = jinja_environment.get_template('templete/managepost.html')
    self.response.out.write(template.render(template_values))

class DeletePost(webapp2.RequestHandler):
  def get(self,post_id):
    template_values={}
    user = users.get_current_user()
    #post_id = self.request.get('id')
    if post_id:
        post = ndb.Key(Post, int(post_id)).get()
        if post.owner==user:
            post.key.delete()
            template_values.update(MyUtil().renderSuccess("Your Article Deleted Successful. Enjoy Blogging!"))
        else:
            template_values.update(MyUtil().renderAlert("You must be the post owner for deleting."))
    else:
        template_values.update(MyUtil().renderAlert("Cannot find post by this id! Please try again later."))
    posts = Post.query(Post.owner==user).order(-Post.publishdatetime)    
    if posts.count()>0:
        template_values.update({'posts':posts})        
        blogid_name={}
        for post in posts:
            thisblog=ndb.Key(Blog, post.blog_id).get()
            blogid_name.update({post.blog_id:thisblog.blogname}) 
        template_values.update({'blogid_name':blogid_name})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/managepost.html')
    self.response.out.write(template.render(template_values))
    
app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/addblog', AddBlog),
  ('/manageblog', ManageBlog),
  ('/deleteblog', DeleteBlog),
  ('/editblog', EditBlog),
  (r'/viewblog/(\d+)', ViewBlog),
  ('/addpost', AddPost),
  ('/managepost', ManagePost),
  (r'/viewpost/(\d+)', ViewPost),  
  ('/savepost',SavePost),
  (r'/editpost/(\d+)', EditPost),
  (r'/deletepost/(\d+)', DeletePost)
])
