from django.contrib import admin
from .models import Currency, Course


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('cur_name', 'cur_abbrev', 'number_unit', 'nbrb_code',
                    'nbrb_code_static', 'cur_date_start', 'cur_date_end')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('date_stamp', 'usd', 'eur', 'rub', 'uah', 'jpy', 'cny')

# Register your models here.
