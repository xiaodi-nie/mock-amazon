# Generated by Django 2.2 on 2019-04-15 17:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ride_share', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tripsharerlist',
            name='trip',
        ),
        migrations.RemoveField(
            model_name='vehicle',
            name='driver',
        ),
        migrations.DeleteModel(
            name='Driver',
        ),
        migrations.DeleteModel(
            name='Trip',
        ),
        migrations.DeleteModel(
            name='TripSharerList',
        ),
        migrations.DeleteModel(
            name='Vehicle',
        ),
    ]
