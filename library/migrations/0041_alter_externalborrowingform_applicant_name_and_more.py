# Generated by Django 4.2.6 on 2023-11-23 07:23

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0035_alter_member_options'),
        ('library', '0040_auto_20220130_1920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalborrowingform',
            name='applicant_name',
            field=models.CharField(editable=False, max_length=200),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='applicant_org',
            field=models.CharField(blank=True, editable=False, max_length=200),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='contact_email',
            field=models.EmailField(editable=False, max_length=254),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='contact_phone',
            field=models.CharField(editable=False, max_length=20),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='due_date',
            field=models.DateField(blank=True, default=None, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='event_details',
            field=models.TextField(editable=False),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='form_status',
            field=models.CharField(choices=[('U', 'Unapproved'), ('D', 'Denied'), ('A', 'Approved'), ('C', 'Completed')], editable=False, max_length=1),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='form_submitted_date',
            field=models.DateField(default=datetime.date.today, editable=False),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='librarian_comments',
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name='externalborrowingform',
            name='requested_borrow_date',
            field=models.DateField(editable=False),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='auth_gatekeeper_borrow',
            field=models.ForeignKey(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorised_borrowing_ext', to='members.member'),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='auth_gatekeeper_return',
            field=models.ForeignKey(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorised_returning_ext', to='members.member'),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='borrower_name',
            field=models.CharField(blank=True, editable=False, max_length=200),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='date_borrowed',
            field=models.DateField(blank=True, default=None, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='date_returned',
            field=models.DateField(blank=True, default=None, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='form',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='requested_items', to='library.externalborrowingform'),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='item',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='ext_borrow_records', to='library.item'),
        ),
        migrations.AlterField(
            model_name='externalborrowingitemrecord',
            name='returner_name',
            field=models.CharField(blank=True, editable=False, max_length=200),
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_external', models.BooleanField(editable=False)),
                ('borrower_name', models.CharField(max_length=200)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_info', models.TextField()),
                ('date_to_borrow', models.DateField()),
                ('date_to_return', models.DateField()),
                ('additional_details', models.TextField(blank=True)),
                ('submitted_datetime', models.DateTimeField(auto_now_add=True)),
                ('approval_status', models.CharField(choices=[('?', 'Pending'), ('A', 'Approved'), ('X', 'Denied'), ('!', 'Completed')], default='?', max_length=1)),
                ('status_update_datetime', models.DateTimeField(blank=True)),
                ('librarian_comments', models.TextField(blank=True)),
                ('active', models.BooleanField(default=False)),
                ('internal_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.member')),
                ('item_borrow_records', models.ManyToManyField(blank=True, to='library.borrowrecord')),
                ('reserved_items', models.ManyToManyField(related_name='reservations', to='library.item')),
            ],
        ),
    ]