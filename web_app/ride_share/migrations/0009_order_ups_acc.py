# Generated by Django 2.2 on 2019-04-23 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride_share', '0008_auto_20190423_0357'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='ups_acc',
            field=models.CharField(blank=True, default='none', max_length=128, verbose_name='ups_acc'),
        ),
    ]
