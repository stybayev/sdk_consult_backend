from django.db import models
from parler.models import TranslatableModel, TranslatedFields


class Programs(TranslatableModel):
    translations = TranslatedFields(
        title=models.CharField(max_length=100,
                               verbose_name='Название программы'),

        descriptions=models.TextField(verbose_name='Описание программы'),

        logo=models.ImageField(upload_to='images/programs/',
                               blank=True, null=True,
                               verbose_name='Логотип программы'),
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Программы"
        verbose_name_plural = "01 Программы"

    @property
    def image_url(self):
        if not self.logo:
            return None
        else:
            return self.logo.url

    @property
    def program_info(self):
        new_dict = dict()
        new_dict['title'] = self.title
        new_dict['descriptions'] = self.descriptions
        new_dict['logo'] = self.image_url
        return new_dict
