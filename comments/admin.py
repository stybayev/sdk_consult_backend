from .models import Comment
from django.contrib import admin


class CommentAdmin(admin.ModelAdmin):
    list_display = ('real_estate', 'text', 'author')


admin.site.register(Comment, CommentAdmin)
