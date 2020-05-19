
from .models import Thread,Comment,ForumCategories,Topics,thread_view
from rest_framework import serializers, fields
from accounts.serializers import UserProfileShortDataSerializer
from core.serializers import Base64ImageField, Base64FileField 
from django.db.models import Q
from core.utils import convert_file_to_base64,convert_file_to_s3url

class CommentSerializer(serializers.ModelSerializer):
    comment_by = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ('id','thread','comment_by','text','created_date','parent_comment', 'subcomments',)
        read_only_fields = ('subtasks',)

        extra_kwargs = {'thread': {'allow_null': False, 'required': True}}

    def get_comment_by(self, obj):
        if obj.comment_by:
            return UserProfileShortDataSerializer(obj.comment_by.userprofile).data

class ThreadCommentsScopeSerializer(serializers.ModelSerializer):
    """
    Serializer for comments and subcomments.
    Use with ThreadSerializer
    """
    subcomments = serializers.SerializerMethodField()
    comment_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'text','created_date','comment_by' ,'subcomments')

    def get_subcomments(self, obj):
        """
        Get current comment subcomments
        """
        serializer = CommentSerializer(
            Comment.objects.filter(parent_comment=obj).order_by('-id'), many=True
        )
        return serializer.data 
        
    def get_comment_by(self, obj):
        if obj.comment_by:
            return UserProfileShortDataSerializer(obj.comment_by.userprofile).data

class ThreadSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    category_title = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField(
        read_only=True, source='get_post_count'
    )
    reply_count = serializers.IntegerField(
        read_only=True, source='get_reply_count'
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Thread
        fields = ('id','owner','title','description','created_date','public','participants','category_title','posts_count','reply_count','image','forumcategories','topics')#,'comment_thread'

    def get_owner(self, obj):
        if obj.owner:
            return UserProfileShortDataSerializer(obj.owner.userprofile).data

    def get_category_title(self, obj):
        if obj.forumcategories:
            return obj.forumcategories.title
    


class ForumCategoriesSerializer(serializers.ModelSerializer):
    """
    Serializer for forum categories
    """
    image = Base64ImageField(required=False, allow_null=True)
    class Meta:
        model = ForumCategories
        fields = ('id','title','description','created_date','image','colortext')  #,'thread_count',,'topics'

    
class TopicsSerializer(serializers.ModelSerializer):
    """
    Serializer for Topics
    """
    thread_count = serializers.IntegerField(
        read_only=True, source='get_thread_count'
    )
    posts_count = serializers.IntegerField(
        read_only=True, source='get_comment_count'
    )
    image = Base64ImageField(required=False, allow_null=True)
    class Meta:
        model = Topics
        fields = ('id','title','description','created_date','image','colortext','category','thread_count','posts_count')  #,'thread_count'

class ThreadScopeSerializer(serializers.ModelSerializer):
    """
    Serializer for thread limited data.
    """
    thread = serializers.SerializerMethodField()
    class Meta:
        model = Topics
        fields = ('id','title','thread')

    def get_thread(self, obj): 
        queryset = Thread.objects.filter(Q(topics_id=obj.id),
                Q(owner=self.context['request'].user) |
                Q(participants=self.context['request'].user) |
                Q(public=True)   
            ).order_by('-id')

        page = self.context.get('view').paginate_queryset(queryset)
        if page is not None: 
            serializer = ThreadSerializer(page, many=True) 
            return self.context.get('view').get_paginated_response(serializer.data).data
        serializer = ThreadSerializer(queryset, many=True)
        return self.context.get('view').get_paginated_response(serializer.data).data

class ThreadCountSerializer(serializers.ModelSerializer):
    """
    Serializer for most viewed thread
    """
    class Meta:
        model = thread_view
        fields = '__all__'


class CommentThreadScopeSerializer(serializers.ModelSerializer):
    """
    Serializer for comments/subcomments based on thread .
    """
    thread_comments = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    class Meta:
        model = Thread
        fields = ('id','title','image','created_date','description','owner','thread_comments')

    def get_thread_comments(self, obj):
        """
         Get current thread comments
        """
        qs = Comment.objects.filter(thread=obj, parent_comment__isnull=True)
        page = self.context.get('view').paginate_queryset(qs)
        if page is not None: 
            serializer = ThreadCommentsScopeSerializer(page, many=True) 
            return self.context.get('view').get_paginated_response(serializer.data).data
        serializer = ThreadCommentsScopeSerializer(qs, many=True)
        return self.context.get('view').get_paginated_response(serializer.data).data

    def get_owner(self, obj):
        if obj.owner:
            return UserProfileShortDataSerializer(obj.owner.userprofile).data