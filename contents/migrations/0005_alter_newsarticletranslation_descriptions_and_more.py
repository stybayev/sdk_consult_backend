# Generated by Django 4.0.1 on 2022-09-18 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contents', '0004_alter_newsarticle_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsarticletranslation',
            name='descriptions',
            field=models.TextField(verbose_name='Полное описание новости'),
        ),
        migrations.AlterField(
            model_name='newsarticletranslation',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/news_article/images/', verbose_name='Изображение новости'),
        ),
        migrations.AlterField(
            model_name='newsarticletranslation',
            name='published_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата публикации'),
        ),
        migrations.AlterField(
            model_name='newsarticletranslation',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Загловок новости'),
        ),
        migrations.AlterField(
            model_name='newsarticletranslation',
            name='url_link',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='URL-ссылка новости'),
        ),
    ]