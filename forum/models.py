from django.db import models
from accounts.models import User
from django.utils import timezone
from django.db.models import Q
from ckeditor.fields import RichTextField
from colorful.fields import RGBColorField


class ForumCategories(models.Model):
    
    title = models.CharField(max_length=100,blank=False,null=True)
    description = models.TextField(blank=False)
    created_date = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='forum/category',null=True)
    colortext = RGBColorField(null=True)
    
    def __str__(self):
        return self.title

class Topics(models.Model):
    category = models.ForeignKey(ForumCategories, related_name='category_topics',null=True)
    title = models.CharField(max_length=100,blank=False,null=True)
    description = models.TextField(blank=False)
    created_date = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='forum/topics',null=True)
    colortext = RGBColorField(null=True)
    
    def __str__(self):
        return self.title
    
    def get_thread_count(self) -> int:
        """
        Count of thread against forum topics
        """
        t_count = Thread.objects.filter(
            Q(public=True) &
            Q(topics=self)
            ).count()

        return t_count

    def get_comment_count(self) -> int:
        """
        Count of comment regarding forum thread
        """
        c_count = Comment.objects.filter(thread__topics=self,parent_comment__isnull=True).count()
        
        return c_count

class Thread(models.Model):
    owner = models.ForeignKey(User, related_name='thread_owner',null=True)
    title = models.CharField(max_length=100,blank=False,null=True)
    description = RichTextField()
    created_date = models.DateTimeField(default=timezone.now)
    participants = models.ManyToManyField(
        User,
        related_name='thread_participant',
        blank=True
    )
    public = models.BooleanField(default=False)
    forumcategories = models.ForeignKey(ForumCategories, related_name='forumcategories_thread',null=True)
    topics = models.ForeignKey(Topics, related_name='forum_topic',null=True)
    image = models.ImageField(upload_to='forum/thread',null=True)

    def __str__(self):
        return self.title

    def get_post_count(self) -> int:
        """
        Count of comment regarding forum thread for post
        """
        c_count = Comment.objects.filter(thread=self,parent_comment__isnull=True).count()
        return c_count
    
    def get_reply_count(self) -> int:
        """
        Count of comment regarding forum thread for reply
        """
        posts = Comment.objects.filter(thread=self,parent_comment__isnull=True).values_list('id', flat=True)
        posts_list = [i for i in posts]
        r_count = Comment.objects.filter(thread=self,parent_comment__in=posts_list).count()
        return r_count


class Comment(models.Model):
    thread = models.ForeignKey(Thread, related_name='thread_comment',null=True)
    comment_by = models.ForeignKey(User, related_name='user_comment',null=True)
    text = RichTextField() #models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    parent_comment = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='subcomments'
    )
    def __str__(self):
        return self.text


class thread_view(models.Model):
    """
    tracking of most viewed thread
    """
    thread = models.ForeignKey(Thread, related_name='thread_view',null=True)
    ip_address= models.CharField(max_length=50,blank=False,null=True)
    created_date = models.DateTimeField(default=timezone.now)