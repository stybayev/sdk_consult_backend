# Generated by Django 4.0.1 on 2022-09-13 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('real_estate', '0006_alter_realestate_real_estate_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='realestate',
            name='real_estate_type',
            field=models.CharField(blank=True, choices=[('apartment', 'Квартира'), ('house', 'Дом')], max_length=100, null=True, verbose_name='Вид недвижимости'),
        ),
    ]
