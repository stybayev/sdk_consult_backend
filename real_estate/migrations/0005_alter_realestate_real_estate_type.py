# Generated by Django 4.0.1 on 2022-09-13 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('real_estate', '0004_alter_images_real_estate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='realestate',
            name='real_estate_type',
            field=models.CharField(blank=True, choices=[('Квартира', 'Квартира'), ('Квартира', 'Квартира')], max_length=100, null=True, verbose_name='Вид недвижимости'),
        ),
    ]
