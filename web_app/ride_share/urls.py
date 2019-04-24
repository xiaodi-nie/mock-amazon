from django.urls import re_path,path
from . import views

app_name = 'ride_share'
urlpatterns = [
    path('', views.home, name='home'),
    re_path(r'^register/$', views.register, name='register'),
    re_path(r'^login/$', views.login, name='login'),
    re_path(r'^logout/', views.logout, name='logout'),
    re_path(r'^user/(?P<pk>\d+)/profile/$', views.profile, name='profile'),
    re_path(r'^user/(?P<pk>\d+)/profile/update/$', views.profile_update, name='profile_update'),
    re_path(r'^user/(?P<pk>\d+)/pwdchange/$', views.pwd_change, name='pwd_change'),
    re_path(r'^user/(?P<pk>\d+)/buy/$', views.buy, name='buy'),
    re_path(r'^query/$', views.query, name='query'),
    re_path(r'^search/$', views.search, name='search'),
    re_path(r'^pay/$', views.pay, name='pay')


]