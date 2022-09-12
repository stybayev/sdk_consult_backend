# Generated by Django 4.0.1 on 2022-09-12 07:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='first_name_cyrillic',
            new_name='first_name',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='first_name_latin',
            new_name='last_name',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_name_cyrillic',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_name_latin',
        ),
    ]