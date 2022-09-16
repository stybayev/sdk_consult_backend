from django.db import models


class Services(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Название услуги')

    description = models.TextField(
        verbose_name='Полное описание услуги'
    )

    order_service = models.CharField(
        max_length=255,
        verbose_name='Заказ услуги для обратной связи')
