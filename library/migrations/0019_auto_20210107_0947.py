# Generated by Django 3.1.4 on 2021-01-07 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0018_auto_20210107_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowrecord',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_records', to='library.item'),
        ),
        migrations.AlterField(
            model_name='externalborrowingrecord',
            name='requested_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ext_borrow_records', to='library.item'),
        ),
    ]
