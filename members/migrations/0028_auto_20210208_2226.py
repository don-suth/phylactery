# Generated by Django 3.1.4 on 2021-02-08 14:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0027_memberflag_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rankassignments',
            name='rank_expired',
        ),
        migrations.AddField(
            model_name='rankassignments',
            name='expired_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='rankassignments',
            name='assignment_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]