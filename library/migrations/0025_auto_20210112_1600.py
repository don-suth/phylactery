# Generated by Django 3.1.4 on 2021-01-12 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('library', '0024_auto_20210112_0153'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ComputedItemTags',
            new_name='ItemComputedTags',
        ),
    ]