import pytest
from assistant import views


@pytest.mark.django_db(transaction=True)
def test_get_period():
    last_day = '2040-01-01'
    early_day = '2000-01-01'
    t_func = views.get_period_courses(last_day, early_day)
    assert t_func == [1]
