from django.db import models

"""
 Модель новостей. Ни одно из полей не обязательно к заполнению. При загрузке изображения файлы 
 сохраняются в директорию media/images/news_article/images/photo.jpeg
 Сортировка идет по полю ordering_number.
 iamge_url - проперти который возвращает относительный url адрес загруженного файла
"""


class NewsArticle(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    descriptions = models.TextField()
    url_link = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='images/news_article/images/', blank=True, null=True)
    ordering_number = models.IntegerField(blank=True, null=True, unique=True)
    published_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "01 Новости"
        ordering = ['ordering_number']

    @property
    def image_url(self):
        if not self.image:
            return None
        else:
            return self.image.url

    """
    Метод проперти который возвращает информацию о новостной статье нужную в апи
    """

    @property
    def article_info(self):
        new_dict = dict()
        new_dict['title'] = self.title
        new_dict['content'] = self.descriptions
        new_dict['url_link'] = self.url_link
        new_dict['ordering_number'] = self.ordering_number
        new_dict['published_date'] = self.published_date
        new_dict['image_url'] = self.image_url
        return new_dict
