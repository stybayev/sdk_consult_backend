from django.contrib import admin
from .models import NewsArticle


class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "ordering_number", "published_date",)


admin.site.register(NewsArticle, NewsArticleAdmin)
