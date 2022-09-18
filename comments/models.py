from django.contrib.auth import get_user_model
from django.db import models


class Comment(models.Model):
    real_estate = models.ForeignKey(
        'real_estate.RealEstate',
        related_name='comments',
        on_delete=models.RESTRICT,
        verbose_name='Недвижимость')

    text = models.TextField(
        verbose_name='Отзыв')

    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.RESTRICT,
        related_name='comments',
        verbose_name='Автор отзыва')

    def __str__(self):
        return f'{self.author} - {self.real_estate}'

    class Meta:
        verbose_name = 'Отзывы клиентов'
        verbose_name_plural = '01 Отзывы клиентов'
