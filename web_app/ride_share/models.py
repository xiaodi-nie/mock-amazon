from django.db import models
from django.contrib.auth.models import User
import django.utils.timezone as timezone
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    is_driver = models.BooleanField(
        'IsDriver', default=False)

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return self.user


class Order(models.Model):
    user_id = models.PositiveSmallIntegerField('user_id', default=0)
    x_pos = models.PositiveSmallIntegerField('x_pos')
    y_pos = models.PositiveSmallIntegerField('y_pos')
    product_name = models.CharField('product_name', max_length=128)
    quantity = models.PositiveSmallIntegerField('quantity', default=0)
    status = models.CharField('status', max_length=128, default='none')
    ups_acc = models.CharField('ups_acc', max_length=128, default='none', blank=True)

    class Meta:
        verbose_name = 'Order'

    def __str__(self):
        return self.pk


class Warehouse(models.Model):
    warehouse_id = models.PositiveSmallIntegerField('warehouse_id', default=0)
    wh_x = models.PositiveSmallIntegerField('wh_x', default=0)
    wh_y = models.PositiveSmallIntegerField('wh_y', default=0)

    class Meta:
        verbose_name = 'Warehouse'

    def __str__(self):
        return self.pk


class Product(models.Model):
    name = models.CharField('name', max_length=128)
    number = models.IntegerField('number', default=0)
    warehouse_id = models.IntegerField('warehouse_id', default=0)

    class Meta:
        verbose_name = 'Product'

    def __str__(self):
        return self.pk


class Ack(models.Model):
    ack_num = models.IntegerField('ack_num', default=0)
    type = models.CharField('type', max_length=128)
    status = models.CharField('status', max_length=128, blank=True)
    class Meta:
        verbose_name = 'Ack'

    def __str__(self):
        return self.pk



class Messageworld(models.Model):
    order_id = models.IntegerField('order_id', default=0)
    message = models.CharField('message', max_length=512)
    type = models.CharField('type', max_length=512)

    class Meta:
        verbose_name = 'Messageworld'

    def __str__(self):
        return self.pk

