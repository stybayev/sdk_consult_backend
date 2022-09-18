# Generated by Django 4.0.1 on 2022-09-18 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contents', '0002_alter_newsarticle_descriptions_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsarticle',
            name='descriptions',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/news_article/images/'),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='ordering_number',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='published_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='url_link',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]