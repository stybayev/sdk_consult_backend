from django.db import models
from parler.models import TranslatableModel, TranslatedFields


class Services(TranslatableModel):
    translations = TranslatedFields(
        title=models.CharField(
            max_length=255,
            verbose_name='Название услуги'),

        description=models.TextField(
            verbose_name='Полное описание услуги'
        ),
    )

    order_service = models.CharField(
        max_length=255,
        verbose_name='Заказ услуги для обратной связи')

    def __str__(self):
        return f'{self.title}'

    @property
    def service_info(self):
        new_dict = dict()
        new_dict['title'] = self.title
        new_dict['description'] = self.description
        new_dict['order_service'] = self.order_service

        return new_dict
