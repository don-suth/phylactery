# Generated by Django 3.1.4 on 2021-02-18 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('library', '0029_externalborrowingrecord_form_submitted_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagparent',
            name='parent_tag',
            field=models.ManyToManyField(blank=True, related_name='children', to='taggit.Tag'),
        ),
    ]
