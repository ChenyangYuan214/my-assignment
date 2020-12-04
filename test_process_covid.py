# -*- coding:utf-8 -*-
import pytest
from jsonschema import validate
import json
from process_covid import hospital_vs_confirmed, generate_data_plot_confirmed, compute_running_average

@pytest.fixture(scope='function')
def setup_function(request):
    def teardown_function():
        print("teardown_function called.")
    request.addfinalizer(teardown_function)
    print('setup_function called.')


def test_hospital_vs_confirmed(setup_function):
    file = open("covid_data/test_hospital_vs_confirmed.json", "rb")
    jsonObejct = json.load(file)
    result = hospital_vs_confirmed(jsonObejct)
    assert len(result[0]) == 4
    assert len(result[1]) == 4
    assert '2020-03-16' not in result[0]
    assert '2020-03-20' not in result[0]


def test_generate_data_plot_confirmed_exception1(setup_function):
    file = open("covid_data/test_hospital_vs_confirmed.json", "rb")
    jsonObejct = json.load(file)
    with pytest.raises(ValueError):
        generate_data_plot_confirmed(jsonObejct, sex = 4, max_age = 65, status ="total")

def test_generate_data_plot_confirmed_exception2(setup_function):
    file = open("covid_data/test_hospital_vs_confirmed.json", "rb")
    jsonObejct = json.load(file)
    with pytest.raises(ValueError):
        generate_data_plot_confirmed(jsonObejct, sex = 'male', max_age = 65, status ="total")

def test_compute_running_average(setup_function):
    array = [0, 1, 5, 2, 2, 5]
    result = [None, 2.0, 2.6666666666666665, 3.0, 3.0, None]
    ans = compute_running_average(array, 3)
    assert ans == result

def test_compute_running_average_None(setup_function):
    array = [2, None, 4]
    result = [None, 3.0, None]
    ans = compute_running_average(array, 3)
    assert ans == result

def test_compute_running_average_even(setup_function):
    array = [2, None, 4]
    result = [None, 3.0, None]
    with pytest.raises(ValueError):
        compute_running_average(array, 6)
    
