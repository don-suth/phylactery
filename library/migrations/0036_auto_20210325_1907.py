# Generated by Django 3.1.6 on 2021-03-25 11:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0035_delete_externalborrowingrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ext_borrow_records', to='library.item'),
        ),
    ]