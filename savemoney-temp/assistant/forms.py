from django import forms
from .models import *


class InputForm(forms.Form):
    """
    Форма для ввода данный.

    Поля:
    cur_abbrev - буквенный код валюты, список берется из экземпляров модели Currency
    time_period - период времени от текущей даты в днях, за который делается анализ
    average_number - количество дней , по которому рассчитывается скользящее среднее
    """
    cur_abbrev = forms.ChoiceField(
        choices=Currency.objects.values_list('cur_abbrev', 'cur_abbrev').distinct(), label='Валюта')
    time_period = forms.IntegerField(min_value=7, label='Глубина анализа, дней')
    average_number = forms.IntegerField(min_value=2, label='Глубина усреднения, дней')
