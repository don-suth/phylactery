# Generated by Django 3.1 on 2020-08-28 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_item_item_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='item_slug',
            field=models.SlugField(null=True),
        ),
    ]