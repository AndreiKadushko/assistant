from django.db import models


class Course(models.Model):
    """
    Модель курсов валют.

    date_stamp - дата
    usd, eur и далее - курс указанной валюты на дату
    """
    date_stamp = models.CharField(max_length=100, primary_key=True)
    usd = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    eur = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    rub = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    uah = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    jpy = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    cny = models.DecimalField(max_digits=6, decimal_places=4, null=True)

    def __str__(self):
        return self.date_stamp


class Currency(models.Model):
    """
    Модель типов валют.

    cur_name - наименование валюты на русском языке;
    cur_abbrev - буквенный код;
    number_unit - количество единиц иностранной валюты;
    nbrb_code - уникальный внутренний код банка для запроса курса;
    nbrb_code_static - код валюты, который используется для связи,
                        при изменениях наименования, количества единиц;
    cur_date_start - дата включения валюты в перечень валют;
    cur_date_end - дата исключения валюты из перечня валют;
    """
    cur_name = models.CharField(max_length=100)
    cur_abbrev = models.CharField(max_length=5)
    number_unit = models.IntegerField()
    nbrb_code = models.CharField(max_length=3, primary_key=True)
    nbrb_code_static = models.CharField(max_length=3)
    cur_date_start = models.CharField(max_length=10)
    cur_date_end = models.CharField(max_length=10)
    objects = models.Manager()

    def __str__(self):
        return self.cur_abbrev
