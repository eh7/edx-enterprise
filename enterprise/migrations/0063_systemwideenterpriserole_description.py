# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-12 17:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise', '0062_add_system_wide_enterprise_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemwideenterpriserole',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
