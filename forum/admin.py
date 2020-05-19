from django.contrib import admin
from .models import Thread,Comment,ForumCategories,Topics


admin.site.register(Thread)
admin.site.register(Comment)
admin.site.register(ForumCategories)
admin.site.register(Topics)