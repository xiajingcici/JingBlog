#Jing Xia jx379 N14739892
#See comments in JingBlog Developer Guide
import cgi
import urllib
import webapp2
import jinja2
import os
import re
import datetime
import PyRSS2Gen as RSS2
import logging

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
#https://developers.google.com/appengine/docs/python/mail/receivingmail   Handling Incoming Email
#from google.appengine.api import images

class Blog(ndb.Model):
  #blog_id = ndb.IntegerProperty() #seems don't need, GAE will create a unique key id every time you insert a new row
  blogname = ndb.StringProperty()
  blog_desc = ndb.StringProperty()
  owner = ndb.UserProperty()
  users = ndb.StringProperty(repeated=True)
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
  
class Photo(db.Model): 
    owner = db.UserProperty()
    #avatar = db.BlobProperty()
    photo = db.BlobProperty()
    createtime = db.DateTimeProperty(auto_now_add=True)

class BlogVisitLog(ndb.Model):
    blog_id = ndb.IntegerProperty()
    user = ndb.UserProperty()
    remote_addr = ndb.StringProperty()    
    url = ndb.StringProperty()
    user_agent = ndb.StringProperty()
    referer = ndb.StringProperty()
    createtime = ndb.DateTimeProperty(auto_now_add=True)
    
class PostVisitLog(ndb.Model):   
    post_id = ndb.IntegerProperty()
    user = ndb.UserProperty()
    remote_addr = ndb.StringProperty()    
    url = ndb.StringProperty()
    user_agent = ndb.StringProperty()
    referer = ndb.StringProperty()
    createtime = ndb.DateTimeProperty(auto_now_add=True) 

class Vote(ndb.Model):
    post_id = ndb.IntegerProperty()
    user = ndb.UserProperty()
    remote_addr = ndb.StringProperty()
    type = ndb.IntegerProperty() # 1 for like and 2 for dislike
    createtime = ndb.DateTimeProperty(auto_now_add=True)

class Follow(ndb.Model):
    blog_id = ndb.IntegerProperty()
    user = ndb.UserProperty()
    
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
    content = content.replace("\n", " <br/>")
    return content;
  def searchText(self,content,keyword):
    if str(keyword).lower() in str(content).lower():
        #logging.info("Find: " + keyword+" in "+content)
        return "yes"
    else:
        #logging.info("NOT Find: " + keyword+" in "+content)
        return None
  def saveBlogViewLog(self,request,user,blog_id):
    if 'Referer' in request.headers:
        refer = request.headers['Referer']
    else: 
        refer = None
    if 'User-Agent' in request.headers:
        user_agent = referer =request.headers['User-Agent']
    else: 
        user_agent = None            
    log = BlogVisitLog(blog_id = int(blog_id), user = user, remote_addr = request.remote_addr, url = request.url, user_agent = user_agent, referer = refer )    
    log.put()
    return None
  def savePostViewLog(self,request,user,post_id):
    if 'Referer' in request.headers:
        refer = request.headers['Referer']
    else:
        refer = None
    if 'User-Agent' in request.headers:
        user_agent = referer =request.headers['User-Agent']
    else:
        user_agent = None     
    log = PostVisitLog(post_id = int(post_id), user = user, remote_addr = request.remote_addr, url = request.url, user_agent = user_agent, referer = refer)    
    log.put()
    return None

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
    #blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    blogs = Blog.query(ndb.OR(Blog.owner==user,Blog.users==str(user.email().lower()))).order(-Blog.createtime)
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

class StatBlog(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()    
    blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    blog_count = {}
    post_count = {}
    blog_posts = {}
    if blogs.count()>0:
        template_values={'blogs':blogs}
        for blog in blogs:
            bvlog = BlogVisitLog.query(BlogVisitLog.blog_id==blog.key.id())
            posts = Post.query(Post.blog_id==blog.key.id())
            blog_count.update({blog.key.id():bvlog.count()})
            blog_posts.update({blog.key.id():posts})
            for post in posts:
                pvlog = PostVisitLog.query(PostVisitLog.post_id==post.key.id())
                post_count.update({post.key.id():pvlog.count()})            
        template_values.update(MyUtil().renderLogin(self.request.uri))
        template_values.update({'blog_count':blog_count,'post_count':post_count,'blog_posts':blog_posts})
        template = jinja_environment.get_template('templete/statblog.html')
        self.response.out.write(template.render(template_values))
    else:
        self.redirect("/manageblog?alert=Cannot find any blog under your account.")
    
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

class RssBlog(webapp2.RequestHandler):
  def get(self,blog_id):
    blog = ndb.Key(Blog, int(blog_id)).get() 
    if not blog:
        self.error(404)
    else:
        rssitems = []
        qry =Post.query(Post.blog_id==blog.key.id()).order(-Post.publishdatetime)
        blogdesc = blog.blog_desc
        if not blogdesc:
            blogdesc = ""
        for post in qry:
            rssitem = RSS2.RSSItem(
             title = post.post_title,
             link = self.request.host_url+"/viewpost/"+str(post.key.id()),
             description = "",
             guid = RSS2.Guid(self.request.host_url+"/viewpost/"+str(post.key.id())),
             pubDate = post.publishdatetime)
            rssitems.append(rssitem)
        rss = RSS2.RSS2(
        title = blog.blogname+"'s Rss feed",
        link = self.request.host_url+"/viewblog/"+str(blog.key.id()),
        description = blogdesc+" A "
                      "JingBlog generated RSS2 feeds",
        lastBuildDate = datetime.datetime.now(),
        generator = "JingBlog Platform",
        items = rssitems)
        rss_xml = rss.to_xml()
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(rss_xml)

class FollowBlog(webapp2.RequestHandler):
  def get(self,blog_id):
    blog = ndb.Key(Blog, int(blog_id)).get() 
    if not blog:
        self.error(404)
    else:
        user = users.get_current_user()
        qry = Follow.query(Follow.blog_id==int(blog_id),Follow.user==user)
        if qry.count()>0:
            self.redirect("/viewblog/"+str(blog_id)+"?warning=Aleady Followed.")
        else:
            follow = Follow(blog_id=int(blog_id),user=user)
            follow.put()
            self.redirect("/viewblog/"+str(blog_id)+"?success=Followed.")

class FollowedBlog(webapp2.RequestHandler):
  def get(self):
    template_values={}
    user = users.get_current_user()
    blogids = []
    qry = Follow.query(Follow.user==user)
    #logging.info("followed qry: " + str(qry.count()))
    if qry.count() >0:
        for follow in qry:
            blogids.append(follow.blog_id)
        posts = Post.query(Post.blog_id.IN(blogids)).order(-Post.publishdatetime)
        #logging.info("followed posts: " + str(blogids))
        #logging.info("followed posts: " + str(posts.count()))
        if posts.count()>0:
            template_values.update({'posts':posts})
            blogid_name={}
            for post in posts:
                thisblog=ndb.Key(Blog, post.blog_id).get()
                blogid_name.update({post.blog_id:thisblog.blogname}) 
            template_values.update({'blogid_name':blogid_name})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    alert = self.request.get('alert')
    if alert:
       template_values.update(MyUtil().renderAlert(alert))    
    warning = self.request.get('warning')
    if warning:
       template_values.update(MyUtil().renderWarning(warning))
    success = self.request.get('success')
    if success:
       template_values.update(MyUtil().renderSuccess(success))
    template = jinja_environment.get_template('templete/followedblog.html')
    self.response.out.write(template.render(template_values))
            
class AuthorizeBlog(webapp2.RequestHandler):
  def get(self,blog_id):
    blog = ndb.Key(Blog, int(blog_id)).get() 
    if not blog:
        self.error(404)
    else:
        user = users.get_current_user()
        if blog.owner !=user:
            self.redirect("/manageblog?alert=You cannot authorize access for other's blog.")
        else:
            template_values={'blog':blog}            
            template = jinja_environment.get_template('templete/authorizeblog.html')
            self.response.out.write(template.render(template_values))
  def post(self,blog_id):
    #blog_id = self.request.get('blog_id')
    blog = ndb.Key(Blog, int(blog_id)).get() 
    if not blog:
        self.error(404)
    else:
        user = users.get_current_user()
        if blog.owner !=user:
            self.redirect("/manageblog?alert=You cannot authorize access for other's blog.")
        else:
            email = self.request.get('email')
            if not blog.users:
                blog.users=[email.lower()]
                blog.put()
                self.redirect("/manageblog?success=This user success Authorized.")
            else:
                if email in blog.users:
                    self.redirect("/manageblog?warning=This user already Authorized.")
                else:
                    blog.users.extend(email.lower())
                    blog.put()
                    self.redirect("/manageblog?success=This user success Authorized.")

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
        user = users.get_current_user()
        MyUtil().saveBlogViewLog(self.request,user,blog_id)
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
            postsin=[]
            for post in qry:
                thiscontent = "".join(post.contents)
                if MyUtil().searchText(thiscontent,search):
                    postsin.append(post)
            if len(postsin)>0:
                template_values.update({'posts':postsin})        
            qry=None
            template_values.update({'searchkeyword':search})        
            #logging.info("qry: " + str(postsin))
            #logging.info("qry: " + str(qry.count()))
        if qry:
            if qry.count(11) > 10:
                old = self.request.get('old')
                if old:
                    posts = qry.fetch(offset=10)
                    template_values.update({'blog':blog,'posts':posts,"old":old})
                else:
                    posts = qry.fetch(10)
                    if tag:
                        oldlink = self.request.uri+"&old=true"
                    else:
                        oldlink = self.request.uri+"?old=true"
                    template_values.update({'blog':blog,'posts':posts,'oldlink':oldlink})            
            elif qry.count() == 0:
                template_values.update({'blog':blog})
            else:
                posts = qry
                template_values.update({'blog':blog,'posts':posts})        
        else:
            template_values.update({'blog':blog})        
        warning = self.request.get('warning')
        if warning:
           template_values.update(MyUtil().renderWarning(warning))
        success = self.request.get('success')
        if success:
           template_values.update(MyUtil().renderSuccess(success))
        template_values.update(MyUtil().renderLogin(self.request.uri))
        template = jinja_environment.get_template('templete/viewblog.html')
        self.response.out.write(template.render(template_values))
        
class AddPost(webapp2.RequestHandler):
  def get(self):    
    template_values={}
    user = users.get_current_user()    
    #logging.info("user_email: " + user_email)
    blogs = Blog.query(ndb.OR(Blog.owner==user,Blog.users==str(user.email().lower()))).order(-Blog.createtime)
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
      if blog.owner !=user and user.email().lower() not in blog.users:
        template_values.update(MyUtil().renderAlert("You are not authorized to add post in this blog."))
      else:
	    oktowrite = True
    else:
      template_values.update(MyUtil().renderAlert("Cannot find the blog you choose. Please try again."))
    if oktowrite:
      chunks, chunk_size = len(post_content), 500
      content_split = [ post_content[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
      tag_split = [x.strip() for x in post_tags.split(',')]
      post = Post(post_title=post_title,blog_id=int(blog_id),owner=blog.owner,contents=content_split,tags=list(set(tag_split)))
      post.put()
      template_values.update(MyUtil().renderSuccess("Your Article Saved Successful. Enjoy Blogging!"))
    #blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    blogs = Blog.query(ndb.OR(Blog.owner==user,Blog.users==str(user.email().lower()))).order(-Blog.createtime)
    if blogs.count()>0:
       template_values.update({'blogs':blogs})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/addpost.html')
    self.response.out.write(template.render(template_values))
 
class ManagePost(webapp2.RequestHandler):
  def get(self):
    template_values={}
    user = users.get_current_user()
    blogids = []
    qry = Blog.query(ndb.OR(Blog.owner==user,Blog.users==user.email().lower()))
    for thisblog in qry:
        blogids.append(thisblog.key.id())
    #posts = Post.query(Post.owner==user).order(-Post.publishdatetime)    
    posts = Post.query(Post.blog_id.IN(blogids)).order(-Post.publishdatetime)    
    if posts.count()>0:
        template_values.update({'posts':posts})
        blogid_name={}
        for post in posts:
            thisblog=ndb.Key(Blog, post.blog_id).get()
            blogid_name.update({post.blog_id:thisblog.blogname}) 
        template_values.update({'blogid_name':blogid_name})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    alert = self.request.get('alert')
    if alert:
       template_values.update(MyUtil().renderAlert(alert))    
    warning = self.request.get('warning')
    if warning:
       template_values.update(MyUtil().renderWarning(warning))
    success = self.request.get('success')
    if success:
       template_values.update(MyUtil().renderSuccess(success))
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
        MyUtil().savePostViewLog(self.request,user,post_id)
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
    upvotes = Vote.query(Vote.post_id==int(post_id) and Vote.type==int(1))
    downvotes = Vote.query(Vote.post_id==int(post_id) and Vote.type==int(2))
    template_values.update({'like_num':upvotes.count(),'notlike_num':downvotes.count()})
    warning = self.request.get('warning')
    if warning:
       template_values.update(MyUtil().renderWarning(warning))
    success = self.request.get('success')
    if success:
       template_values.update(MyUtil().renderSuccess(success))
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/viewpost.html')
    self.response.out.write(template.render(template_values))

class VoteUpPost(webapp2.RequestHandler):
  def get(self,post_id):
    template_values={}
    user = users.get_current_user()
    remote_addr = self.request.remote_addr
    post = ndb.Key(Post, int(post_id)).get()
    if post:
        votes = Vote.query(ndb.AND(Vote.post_id==int(post_id),ndb.OR(Vote.user==user,Vote.remote_addr==remote_addr)))
        if votes.count()>0:
            self.redirect("/viewpost/"+str(post_id)+"?warning=You already voted.")
        else:
            vote = Vote(post_id =int(post_id),user = user, remote_addr = remote_addr,type = int(1))
            vote.put()
            self.redirect("/viewpost/"+str(post_id)+"?success=Voted.")
    else:
        self.error(404)

class VoteDownPost(webapp2.RequestHandler):
  def get(self,post_id):
    template_values={}
    user = users.get_current_user()
    remote_addr = self.request.remote_addr
    post = ndb.Key(Post, int(post_id)).get()
    if post:
        votes = Vote.query(Vote.user==user or Vote.remote_addr==remote_addr)
        if votes.count()>0:
            self.redirect("/viewpost/"+str(post_id)+"?warning=You already voted.")
        else:
            vote = Vote(post_id =int(post_id),user = user, remote_addr = remote_addr,type = int(2))
            vote.put()
            self.redirect("/viewpost/"+str(post_id)+"?success=Voted.")
    else:
        self.error(404)
    
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
    #blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
    blogs = Blog.query(ndb.OR(Blog.owner==user,Blog.users==str(user.email().lower()))).order(-Blog.createtime)
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
      if blog.owner !=user and user.email().lower() not in blog.users:
        self.redirect("/managepost?alert=You are not authorized to edit this post.")
        #template_values.update(MyUtil().renderAlert("You are not authorized to add post in this blog."))
      else:
	    oktowrite = True
    else:
      #template_values.update(MyUtil().renderAlert("Cannot find the blog you choose. Please try again."))
      self.redirect("/managepost?alert=Cannot find the blog you choose. Please try again.")
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
      self.redirect("/managepost?success=Your Article Saved Successful. Enjoy Blogging!")

class DeletePost(webapp2.RequestHandler):
  def get(self,post_id):
    template_values={}
    user = users.get_current_user()
    #post_id = self.request.get('id')
    if post_id:
        post = ndb.Key(Post, int(post_id)).get()
        if post.owner==user:
            post.key.delete()
            self.redirect("/managepost?success=Your Article Deleted Successful. Enjoy Blogging!")
            #template_values.update(MyUtil().renderSuccess("Your Article Deleted Successful. Enjoy Blogging!"))
        else:
            self.redirect("/managepost?alert=You must be the post owner for deleting.")
            #template_values.update(MyUtil().renderAlert("You must be the post owner for deleting."))
    else:
        template_values.update(MyUtil().renderAlert("Cannot find post by this id! Please try again later."))
        self.redirect("/managepost?alert=Cannot find post by this id! Please try again later.")
    
class UploadPhoto(webapp2.RequestHandler):
  def get(self):    
    template_values={}
    user = users.get_current_user()
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/uploadimg.html')
    self.response.out.write(template.render(template_values))
  def post(self):
    template_values={}
    img = self.request.get('img')
    img_name = self.request.POST["img"].filename
    if img_name.lower().endswith("jpg") or img_name.lower().endswith("png") or img_name.lower().endswith("gif"):        
        if img:
            user = users.get_current_user()
            photo = Photo()
            photo.owner = user
            photo.photo = db.Blob(img)
            #photo.avatar = db.Blob(images.resize(img, 100, 100))
            photo.put()
            template_values.update(MyUtil().renderSuccess("Your Image Uploaded Successful. Enjoy Blogging!"))
        else:
            template_values.update(MyUtil().renderAlert("Plase choose the image you want to upload."))
    else:
        template_values.update(MyUtil().renderAlert("Only jpg,png and/or gif photo are allowed to upload."))        
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/uploadimg.html')
    self.response.out.write(template.render(template_values))
 
class ManagePhoto(webapp2.RequestHandler):
  def get(self):    
    template_values={}
    user = users.get_current_user()
    photos = Photo.all()
    photos.filter('owner =', user).order('-createtime')    
    if photos.count()>0:
        template_values.update({'photos':photos,'domain':self.request.host_url})
    else:
        template_values.update({'domain':self.request.host_url})    
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/managephoto.html')
    self.response.out.write(template.render(template_values))

class DeletePhoto(webapp2.RequestHandler):
  def get(self,img_key):    
    template_values={}
    user = users.get_current_user()
    photo = db.get(img_key)
    if photo:
        if photo.owner == user:
            db.delete(photo)
        else:
            template_values.update(MyUtil().renderAlert("You cannot delete a photo that not belongs to you."))
    else:
        template_values.update(MyUtil().renderAlert("Cannot find the photo you are looking for."))
    photos = Photo.all()
    photos.filter('owner =', user).order('-createtime')   
    if photos.count()>0:
        template_values.update({'photos':photos,'domain':self.request.host_url})
    else:
        template_values.update({'domain':self.request.host_url})
    template_values.update(MyUtil().renderLogin(self.request.uri))
    template = jinja_environment.get_template('templete/managephoto.html')
    self.response.out.write(template.render(template_values))
    
class Image(webapp2.RequestHandler):
    def get(self,img_key):
        photo = db.get(img_key)
        if photo.photo:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(photo.photo)
        else:
            self.error(404)    

class PostHandler(InboundMailHandler):
    def receive(self, mail_message):        
        sender = mail_message.sender
        user = users.User(sender)
        subject = mail_message.subject 
        plaintext_bodies = mail_message.bodies('text/plain')
        for content_type, body in plaintext_bodies:
            body_text = body.decode()
            break
        #logging.info("user.email(): " + user.email().lower())
        message = mail.EmailMessage(sender="Post on JingBlog <post@jingblogost.appspotmail.com>",
                            subject="About your post on JingBlog")
        message.to = sender
        message.body = ""
        #blogs = Blog.query(Blog.owner==user).order(-Blog.createtime)
        qry = Blog.query().order(-Blog.createtime)
        if "@" in subject:
            subjects = subject.split("@")
            title = subjects[0]
            blog_name = subjects[1]
        blogs = []
        thisnameblog = None
        for blog in qry:
            if blog.owner.email().lower()== user.email().lower():
                blogs.append(blog)
                if blog.blogname == blog_name:
                    thisnameblog = blog
            elif user.email().lower() in blog.users:
                blogs.append(blog)
                if blog.blogname == blog_name:
                    thisnameblog = blog
        if thisnameblog:
            blog = thisnameblog            
        else:
            for thisblog in blogs:
                blog = thisblog
        if blog:
            chunks, chunk_size = len(str(body_text)), 500
            content_split = [ str(body_text)[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
            #tag_split = [x.strip() for x in post_tags.split(',')]
            post = Post(post_title=title,blog_id=blog.key.id(),owner=user,contents=content_split)
            post.put()
            message.body="Post posted on your blog "+blog.blogname+"\n"
        else:
            message.body="You don't have any blog yet. \nPlease create one on JingBlog Platform. \nView JingBlog Platform on "+self.request.host_url
        message.send()
        
app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/addblog', AddBlog),
  ('/manageblog', ManageBlog),
  ('/followedblog', FollowedBlog),
  ('/deleteblog', DeleteBlog),
  ('/editblog', EditBlog),
  (r'/viewblog/(\d+)', ViewBlog),
  ('/statisticsblog', StatBlog),  
  (r'/rssblog/(\d+)', RssBlog),
  (r'/followblog/(\d+)', FollowBlog),  
  (r'/authorizeblog/(\d+)', AuthorizeBlog),
  ('/addpost', AddPost),
  ('/managepost', ManagePost),
  (r'/viewpost/(\d+)', ViewPost),  
  (r'/voteuppost/(\d+)', VoteUpPost),
  (r'/votedownpost/(\d+)', VoteDownPost),
  ('/savepost',SavePost),
  (r'/editpost/(\d+)', EditPost),
  (r'/deletepost/(\d+)', DeletePost),
  ('/uploadphoto',UploadPhoto),
  ('/managephoto',ManagePhoto),
  (r'/deleteimg/([A-Za-z0-9\-]+)', DeletePhoto),
  (r'/img/([A-Za-z0-9\-]+)',Image),
  PostHandler.mapping()
], debug=True)
