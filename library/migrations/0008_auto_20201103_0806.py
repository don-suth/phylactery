# Generated by Django 3.1 on 2020-11-03 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_strtagvalue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strtagthrough',
            name='value',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='library.strtagvalue'),
        ),
    ]
