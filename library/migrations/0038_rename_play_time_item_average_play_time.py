# Generated by Django 3.2.11 on 2022-01-20 04:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0037_auto_20210330_1354'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='play_time',
            new_name='average_play_time',
        ),
    ]
