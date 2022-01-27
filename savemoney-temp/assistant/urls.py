from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    # currencies viwes
    path('', views.main, name='main'),
    path('currency/', views.course_list, name='course_list'),
    path('about/', views.about, name='about'),
]
