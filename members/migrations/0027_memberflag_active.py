# Generated by Django 3.1.4 on 2021-01-29 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_auto_20210124_0517'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberflag',
            name='active',
            field=models.BooleanField(default=True, help_text='Control whether this flag appears on membership forms'),
        ),
    ]