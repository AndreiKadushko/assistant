import requests
import datetime

from django.shortcuts import render

from .forms import InputForm
from .models import Course, Currency
from django.core.paginator import Paginator


def get_curr_status():
    """
    Получение текущего статуса списка валют.

    Из банка получается полный перечень валюты, для которых установлены курсы белорусского рубля.
    Из этого перечня по наименованию полей в модели Corse выбирается перечень валют и формируется
    актуальное состояние кодов, количества и т.д. в модели Currency.
    """
    set_my_currency = set(field.name.upper() for field in Course._meta.get_fields())
    set_nbrb_codes = set(note.get('nbrb_code') for note in Currency.objects.values('nbrb_code'))
    list_currencies = requests.get('https://www.nbrb.by/api/exrates/currencies')
    json_list_currencies = list_currencies.json()
    #
    for each_currency in json_list_currencies:
        name_currency = each_currency['Cur_Abbreviation']
        in_code = each_currency['Cur_ID']
        #
        if name_currency in set_my_currency and (str(in_code) not in set_nbrb_codes):
            Currency.objects.create(cur_name=each_currency['Cur_Name'],
                                    cur_abbrev=name_currency,
                                    number_unit=each_currency['Cur_Scale'],
                                    nbrb_code=in_code,
                                    nbrb_code_static=each_currency['Cur_ParentID'],
                                    cur_date_start=each_currency['Cur_DateStart'][:10],
                                    cur_date_end=each_currency['Cur_DateEnd'][:10])


def get_day_course(in_date):
    """Получение ежедневного курса валюты.

    Получается перечень курсов по всем видам валют НБРБ, из которого выбираются
    курсы валют из модели Course.
    """
    set_my_currency = set(field.name for field in Course._meta.get_fields())
    http_req = f'https://www.nbrb.by/api/exrates/rates?ondate={in_date}&periodicity=0'
    courses_now = requests.get(http_req)
    json_courses_now = courses_now.json()
    currency_dict = {}
    for each_currency in json_courses_now:
        name_currency = each_currency['Cur_Abbreviation'].lower()
        # Getting courses if they're the fields of the Course model
        if name_currency in set_my_currency:
            currency_dict[name_currency] = each_currency['Cur_OfficialRate']
    Course.objects.create(date_stamp=in_date,
                          usd=currency_dict.get('usd'),
                          eur=currency_dict.get('eur'),
                          rub=currency_dict.get('rub'),
                          uah=currency_dict.get('uah'),
                          jpy=currency_dict.get('jpy'),
                          cny=currency_dict.get('cny'))


def get_period(query_list, last_day, early_day):
    """
    Получение списка периодов действия внутреннего кода валюты с учетом заданных
    временных границ запроса.
    """
    http_query_dict = {}
    for unit in query_list:
        cur_date_end = unit.get('cur_date_end')
        cur_date_start = unit.get('cur_date_start')
        nbrb_code = unit.get('nbrb_code')
        if cur_date_start <= last_day <= cur_date_end:
            if cur_date_start <= early_day <= cur_date_end:
                http_query_dict[nbrb_code] = [last_day, early_day]
                break
            else:
                http_query_dict[nbrb_code] = [last_day, cur_date_start]
        if cur_date_end <= last_day:
            if cur_date_start <= early_day <= cur_date_end:
                http_query_dict[nbrb_code] = [cur_date_end, early_day]
                break
            else:
                http_query_dict[nbrb_code] = [cur_date_end, cur_date_start]
    return http_query_dict


def get_date(str_date):
    """Преобразование строковой даты в формат Date."""
    out_date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
    return out_date


def get_http_strings(http_query_dict):
    """
    Составление строки http-запроса.

    Формирование строки http-запроса из переданного словаря, где ключи -
    это внутренний код валюты банка, значения - период его действия.
    Периоды должны быть не более 365 дней.
    """
    list_http = []
    for key_item in http_query_dict.keys():
        cur_id = key_item
        startdate = http_query_dict.get(cur_id)[1]
        enddate = http_query_dict.get(cur_id)[0]
        startdate_date = get_date(startdate)
        enddate_date = get_date(enddate)
        middle_date = startdate_date + datetime.timedelta(days=364)
        while middle_date < enddate_date:
            http_string = f'https://www.nbrb.by/api/exrates/rates/dynamics/{cur_id}?' \
                          f'startdate={str(startdate_date)}&enddate={str(middle_date)}'
            list_http.append(http_string)
            startdate_date = middle_date + datetime.timedelta(days=1)
            middle_date += datetime.timedelta(days=365)
        http_string = f'https://www.nbrb.by/api/exrates/rates/dynamics/{cur_id}?' \
                      f'startdate={str(startdate_date)}&enddate={str(enddate_date)}'
        list_http.append(http_string)
    return list_http


def get_periods(last_day, early_day):
    """
    Составление адресов http-запроса.

    Формирование адресов http-запросов по каждой валюте отдельно за определенный период времени.
    last_day, early_day - границы запрашиваемого периода.
    """
    query_set_code_static = Currency.objects.values_list('nbrb_code_static', flat=True)
    list_code_static = list(query_set_code_static.distinct())
    dict_http = {}
    for code_static in list_code_static:
        query_items = Currency.objects.filter(nbrb_code_static=code_static).\
            order_by('-cur_date_end')
        query_list = list(query_items.values('nbrb_code', 'cur_date_end', 'cur_date_start'))
        http_query_dict = get_period(query_list, last_day, early_day)
        dict_http[code_static] = get_http_strings(http_query_dict)
    return dict_http


def request_courses(str_http):
    """Выполнение http-запроса."""
    period_course = requests.get(str_http)
    return period_course.json()


def get_courses(dict_http):
    """Получение курсов валют за период и запись в базу Course."""
    for key_item in dict_http.keys():
        filter_note = Currency.objects.filter(nbrb_code_static=key_item)
        cur_name = filter_note[0].cur_abbrev.lower()
        for values_item in dict_http.get(key_item):
            course = request_courses(values_item)
            for item_list in course:
                Course.objects.update_or_create(date_stamp=item_list.get('Date')[:10],
                                                defaults={cur_name: item_list.get('Cur_OfficialRate')})
    return course


def check_missing_entry():
    """
    Проверка отсутствующих записей.

    API банка предусматривает разные процедуры при запросе курсов валют.
    Если за один день - запрос курсов за последний день. При в ответе все валюты.
    Если несколько дней - запрос по отсутствующим дням по каждой валюте по внутреннему коду банка.
    numb_days - первоначальное количество записей в таблице курсов
    """
    date_now = datetime.date.today()
    if Course.objects.count() == 0:
        numb_days = 100  # Период, за который берутся курсы валют
        dict_http = get_periods(str(date_now), str(date_now - datetime.timedelta(days=numb_days)))
        get_courses(dict_http)
    else:
        last_note = Course.objects.last()
        last_note_date = get_date(last_note.date_stamp)
        date_delta = date_now - last_note_date
        if date_delta.days == 1:
            get_day_course(str(date_now))
        elif date_delta.days > 1:
            dict_http = get_periods(str(date_now), str(last_note_date))
            get_courses(dict_http)


def get_list_data(form_date):
    """Получение курса валюты по данным, введенным в форме."""
    date_now = datetime.date.today()
    date_early = str(date_now - datetime.timedelta(days=form_date.get('time_period')))
    query_set_date_stamp = Course.objects.filter(date_stamp__gte=date_early).order_by('-date_stamp')

    list_course = list(query_set_date_stamp.values_list(form_date.get('cur_abbrev').lower(), 'date_stamp'))
    return list_course


def get_increase(list_date):
    """Расчет коэффициента роста за заданный период."""
    len_list = len(list_date)
    prev_cours_item = list_date[len_list - 1][0]
    last_course_item = list_date[0][0]
    increase_coef = last_course_item / prev_cours_item
    increase_coef = f'{increase_coef:7.4f}'
    return increase_coef


def get_trend(form_clean, len_list, list_date_course):
    """Определение тренда методом скользящей средней."""
    block_num = form_clean.get('average_number')
    trend_list = []
    if len_list + 1 > block_num:
        num_note = block_num // 2
        for item_trend in range(len_list - block_num):
            date_out_date = get_date(list_date_course[num_note - 1][1])
            num_note += 1
            new_note = 1
            for item_block in range(block_num):
                new_note *= list_date_course[item_trend + item_block][0]
            new_note = float(new_note) ** (1 / block_num)
            new_note = f'{new_note:7.4f}'
            trend_note = (new_note, str(date_out_date))
            trend_list.append(trend_note)
    else:
        # Обработка неправильного времени усреднения
        pass
    return trend_list


menu = [{'title': 'Главная страница', 'url_name': 'assistant:main'},
        {'title': 'Курсы валют', 'url_name': 'assistant:course_list'},
        {'title': 'О сайте', 'url_name': 'assistant:about'}
        ]


def main(request):
    """
    Открытие главной страницы.

    При этом производится обновление статуса валют (Currency), поиск недостающих записей.
    Если не хватает сегодняшней - запрашиваются ежедневные курсы.
    Если не хватает за период - запрашивается за период по каждой валюте отдельно.
    Если все записи в базе есть, запросы на сервер НБРБ не выполняются.
    После ввода правильных данных в форму рассчитываются и выводятся Коэффициент роста и
    тренд по выбранной валюте.
    """
    get_curr_status()
    check_missing_entry()
    trend_list = []
    form_clean = {}
    increase_coef = 1
    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            form_clean = form.cleaned_data
            list_date_course = get_list_data(form_clean)
            len_list = len(list_date_course)

            increase_coef = get_increase(list_date_course)

            trend_list = get_trend(form_clean, len_list, list_date_course)
        else:
            pass
    else:
        form = InputForm()
    return render(request, 'assistant/main.html', {'title': 'Главная страница',
                                                   'menu': menu,
                                                   'form': form,
                                                   'trend_list': trend_list,
                                                   'cur_abbrev': form_clean.get('cur_abbrev'),
                                                   'increase_coef': increase_coef
                                                   })


def course_list(request):
    courses = Course.objects.order_by('-date_stamp')
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'assistant/currency/list.html',
                  {'page_obj': page_obj, 'title': 'Курсы валют', 'menu': menu})


def about(request):
    return render(request, 'assistant/about/about.html', {'title': 'О сайте', 'menu': menu})
