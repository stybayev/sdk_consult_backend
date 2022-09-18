from django.contrib import admin
from .models import NewsArticle
from parler.admin import TranslatableAdmin


class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'descriptions', 'published_date',)


admin.site.register(NewsArticle, TranslatableAdmin)


