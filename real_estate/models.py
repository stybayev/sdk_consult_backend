from django.contrib.auth import get_user_model
from django.db import models


class RealEstate(models.Model):
    REAL_ESTATE_TYPE_CHOICES = [('apartment', 'Квартира'),
                                ('house', 'Дом')]

    PRIMARY_SECONDARY_CHOICES = [('primary', 'Первичный'),
                                 ('secondary', 'Втооричный')]

    GLAZED_BALCONY_CHOICES = [('open', 'Открытый'),
                              ('glazed', 'Застекленный')]

    real_estate_type = models.CharField(
        choices=REAL_ESTATE_TYPE_CHOICES,
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Вид недвижимости'
    )

    district_city = models.ForeignKey(
        'real_estate.CityDistricts',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='city_districts',
        verbose_name='Район города', )

    number_of_rooms = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name='Количество комнат')

    price = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Цена'
    )

    subject_to_mortgage = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Подлежание ипотеки', )

    primary_secondary = models.CharField(
        choices=PRIMARY_SECONDARY_CHOICES,
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Первичный/Вторичный'
    )

    year_of_construction = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Год постройки', )

    floor = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name='Этаж')

    presence_balcony = models.BooleanField(
        default=True,
        verbose_name='Наличие балкона')

    glazed_balcony = models.CharField(
        choices=GLAZED_BALCONY_CHOICES,
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Застекленность балкона'
    )

    number_of_bathrooms = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Количество санузлов')

    number_of_square_meters = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Количество квадратных метров')

    current_state = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Текущее состояние',
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание'
    )

    users = models.ManyToManyField(
        get_user_model(),
        related_name='favorite',
        null=True,
        blank=True,
        verbose_name='Пользователи, у которых данная недвиэимость в избарнных')

    @property
    def real_estate_info(self):
        dict_info = dict()
        dict_info['real_estate_type'] = self.real_estate_type
        dict_info['number_of_rooms'] = self.number_of_rooms
        dict_info['price'] = self.price
        dict_info['subject_to_mortgage'] = self.subject_to_mortgage
        dict_info['primary_secondary'] = self.primary_secondary
        dict_info['year_of_construction'] = self.year_of_construction
        dict_info['floor'] = self.floor
        dict_info['presence_balcony'] = self.presence_balcony
        dict_info['glazed_balcony'] = self.glazed_balcony
        dict_info['number_of_bathrooms'] = self.number_of_bathrooms
        dict_info['number_of_square_meters'] = self.number_of_square_meters
        dict_info['current_state'] = self.current_state
        dict_info['description'] = self.description
        return dict_info

    def __str__(self):
        return f'{self.real_estate_type} - {self.district_city}'

    class Meta:
        verbose_name = "Недвижимость"
        verbose_name_plural = "01 Недвижимости"


class CityDistricts(models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Район"
        verbose_name_plural = "02 Районы"

    def __str__(self):
        return self.title


class Images(models.Model):
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to='images/real_estate/',
        verbose_name='Фото'
    )

    real_estate = models.ForeignKey(
        'real_estate.RealEstate',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images',
        verbose_name='Квартира'
    )

    def __str__(self):
        return f'{self.image.url}'

    class Meta:
        verbose_name = "Фото"
        verbose_name_plural = "03 Фотографии недвижимости"
