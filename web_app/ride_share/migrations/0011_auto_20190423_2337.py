# Generated by Django 2.2 on 2019-04-23 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride_share', '0010_auto_20190423_2334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='quantity',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='quantity'),
        ),
    ]
