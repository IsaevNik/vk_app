# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-31 22:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0009_cashsend'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashsend',
            name='payment_id',
            field=models.CharField(db_index=True, max_length=16),
        ),
    ]