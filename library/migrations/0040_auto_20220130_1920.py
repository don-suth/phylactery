# Generated by Django 3.2.11 on 2022-01-30 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0039_auto_20220120_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowrecord',
            name='member_address',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='borrowrecord',
            name='member_phone_number',
            field=models.CharField(max_length=20, null=True),
        ),
    ]