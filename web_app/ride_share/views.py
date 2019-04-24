from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import UserProfile, Order, Product
# from .forms import RegistrationForm, LoginForm
from .forms import RegistrationForm, LoginForm, ProfileForm, PwdChangeForm, BuyForm, QueryForm, SearchForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from datetime import datetime, timedelta
import json
import socket

from .world_amazon_pb2 import *
#!/usr/bin/env python3
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import socket
import time

import sys
HOST = "amazondaemon"
PORT = 33333


def receive_from_web(s):
    from_web = ''
    while True:
        print("accepted from daemon")
        data = s.recv(1024)
        if not data:
            break
        from_web += data.decode('ascii')

    print("received from the web ", from_web)
    return from_web


def connectDaemon(message):
    msg = ''
    data = str(message)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print("connect to server")
        s.send(data.encode())
        print("Sent data to server!")

        # from_web = ''
        # while True:
        #
        #     data = s.recv(1024)
        #     print("accepted from daemon")
        #     if not data:
        #         break
        #     from_web += data.decode('ascii')
        #
        # print("received from the web ", from_web)

        s.close()
    except Exception as e:
        print("socket connect and send message fail")
        print(e)
    return msg


def home(request):
    return render(request, 'ride_share/home.html')


def pay(request):
    return render(request, 'ride_share/pay.html')


def register(request):
    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']

            # 使用内置User自带create_user方法创建用户，不需要使用save()
            user = User.objects.create_user(username=username, password=password, email=email)

            # 如果直接使用objects.create()方法后不需要使用save()
            user_profile = UserProfile(user=user)
            user_profile.save()

            return HttpResponseRedirect("/login/")

    else:
        form = RegistrationForm()

    return render(request, 'ride_share/registration.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('ride_share:profile', args=[user.id]))

            else:
                # 登陆失败
                  return render(request, 'ride_share/login.html', {'form': form,
                               'message': 'Wrong password. Please try again.'})
    else:
        form = LoginForm()

    return render(request, 'ride_share/login.html', {'form': form})


@login_required
def profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'ride_share/profile.html', {'user': user})


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


@login_required
def profile_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = ProfileForm(request.POST)

        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            return HttpResponseRedirect(reverse('ride_share:profile', args=[user.id]))
    else:
        default_data = {'first_name': user.first_name, 'last_name': user.last_name,
                         }
        form = ProfileForm(default_data)

    return render(request, 'ride_share/profile_update.html', {'form': form, 'user': user})


@login_required
def pwd_change(request, pk):

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = PwdChangeForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data['old_password']
            username = user.username

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                new_password = form.cleaned_data['password2']
                user.set_password(new_password)
                user.save()
                return HttpResponseRedirect("/accounts/login/")

            else:
                return render(request, 'ride_share/pwd_change.html', {'form': form,
        'user': user, 'message': 'Old password is wrong. Try again'})
    else:
        form = PwdChangeForm()

    return render(request, 'ride_share/pwd_change.html', {'form': form, 'user': user})


def buy(request, pk):
    user = get_object_or_404(User, pk=pk)
    print(user.pk)
    if request.method == "POST":
        form = BuyForm(request.POST)

        if form.is_valid():
            x_pos = form.cleaned_data['x_pos']
            y_pos = form.cleaned_data['y_pos']
            product_name = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            ups_acc = form.cleaned_data['ups_acc']
            products = Product.objects.filter(name=product_name, number__gte=quantity)
            if not products.exists():
                return render(request, 'ride_share/buy.html', {'form': form, 'message':
                    'Out of stock. We will restock and deliver to you soon.'})
            order = Order(user_id=pk, x_pos=x_pos, y_pos=y_pos, product_name=product_name, quantity=quantity,
                          status='none', ups_acc=ups_acc)
            order.save()
            order_id = order.pk
            print("ready to call connect daemon function")
            msg = connectDaemon(order_id)
            print("in web side, recved message is ", msg)
            if msg == "serror":
                return render(request, 'ride_share/buy.html', {'form': form, 'message':
                    'buy order fail. please try again.'})
            else:

                owner_email = user.email
                send_mail('Order confirmed',
                          'Order trip is confirmed, your order id is ' + str(order_id), 'allofprogramming551@gmail.com',
                          [owner_email], fail_silently=False)
                return render(request, 'ride_share/buy.html', {'form': form, 'message':
                    'success buy the product, your order ID is ' + str(order.pk)})


        return render(request, 'ride_share/buy.html', {'form': form, 'message': 'error occur'})
    else:
        form = BuyForm()
    return render(request, 'ride_share/buy.html', {'form': form})


def query(request):
    if request.method == "POST":
        form = QueryForm(request.POST)

        if form.is_valid():
            order_id = form.cleaned_data['order_id']
            orders = Order.objects.filter(pk=order_id)

            if orders.exists():
                order = orders.all()[:1].get()
                message = "query "+str(order_id)
                msg = connectDaemon(message)
                return render(request, 'ride_share/order_info.html', {'order': order})
        return render(request, 'ride_share/query.html', {'form': form, 'message': 'order does not exist'})
    else:
        form = QueryForm()
    return render(request, 'ride_share/query.html', {'form': form})


def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data['productName']
            products = Product.objects.filter(name=product_name)
            if products.exists():
                product = products[0]
                quantity = product.number
                return render(request, 'ride_share/search.html',
                              {'form': form, 'message': 'yes we have this product, the quantity is '+str(quantity)})
            else:
                return render(request, 'ride_share/search.html',
                              {'form': form,
                        'message': 'We do not have this product currently. Later on we may provide this product.'})
    else:
        form = SearchForm()
    return render(request, 'ride_share/search.html', {'form': form})
