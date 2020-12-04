# FIXME add needed imports
from matplotlib import pyplot as plt 
import json
from pathlib import Path


def load_covid_data(filepath):
    file = open(filepath, "rb")
    jsonObejct = json.load(file)
    return jsonObejct

def cases_per_population_by_age(input_data):
    result = {}
    totalPopulation = input_data["region"]["population"]["total"]
    ageBins = input_data["metadata"]["age_binning"]["population"]
    dates = input_data["evolution"]
    for age in ageBins:
        result[age] = []
    for date in dates.keys():
        for i in range(len(ageBins)):
            confirmed = dates[date]["epidemiology"]["confirmed"]["total"]["age"][i]
            percentage = confirmed / totalPopulation
            result[ageBins[i]].append((date, percentage))
    return result

def hospital_vs_confirmed(input_data):
    d = []
    r = []
    dates = input_data["evolution"]
    for date in dates.keys():
        try:
            newConfirmed = dates[date]["epidemiology"]["confirmed"]["new"]["all"]
            newHospitalized = dates[date]["hospitalizations"]["hospitalized"]["new"]["all"]
        except KeyError:
            continue
        ratio = newHospitalized/newConfirmed
        r.append(ratio)
        d.append(date)
    return (d,r)


def generate_data_plot_confirmed(input_data, sex, max_age, status):
    """
    At most one of sex or max_age allowed at a time.
    sex: only 'male' or 'female'
    max_age: sums all bins below this value, including the one it is in.
    status: 'new' or 'total' (default: 'total')
    """
    if sex is not None and max_age is not None:
        raise ValueError("At most one of sex or max_age allowed at a time")
    if sex is not None and sex not in ['male', 'female']:
        raise ValueError("sex should be only 'male' or 'female'")
    
    dates = input_data["evolution"]
    d = []
    v = []
    result = {}
    upperlimit = ''
    if sex is not None:
        for date in dates.keys():
            confirmed = dates[date]["epidemiology"]["confirmed"][status][sex]
            d.append(date)
            v.append(confirmed)
    if max_age is not None:
        ageBins = input_data["metadata"]["age_binning"]["population"]
        N = 0 # max_age in which bin ?
        for bin in ageBins:
            max = bin.split("-")[1]
            if max == '':
                upperlimit = str(max_age)
                break
            if max_age > int(max):
                N += 1
            else:
                upperlimit = max
                break
        for date in dates.keys():
            ageData = dates[date]["epidemiology"]["confirmed"][status]["age"]
            confirmed  = 0
            for i in range(0, N +1 ):  # max_age in the Nth bin
                confirmed += ageData[i]
            d.append(date)
            v.append(confirmed)
    result["date"] = d
    result["value"] = v
    return result, upperlimit


def create_confirmed_plot(input_data, sex=False, max_ages=[], status="total", save=...):
    if sex is True and len(max_ages) > 0:
        raise ValueError("At most one of sex or max_age allowed at a time.")
    fig = plt.figure(figsize=(10, 10))
    if sex:
        lines = []
        for sex in ['male', 'female']:
            obj, upperlimit = generate_data_plot_confirmed(input_data, sex = sex, max_age = None, status = status)
            if sex == 'male':
                line, =plt.plot('date', 'value', color='green', label=status+" "+ sex , data = obj)
                lines.append(line)
            else:
                line, = plt.plot('date', 'value', color='purple', label=status+" "+ sex, data = obj)
                lines.append(line)
        plt.legend(handles = lines)
    if sex is False and len(max_ages) > 0:
        lines = []
        for age in max_ages:
            obj, upperlimit = generate_data_plot_confirmed(input_data, max_age = age, sex = None, status = status) 
            if age <= 25:
                line, =plt.plot('date', 'value', color='green', label=status+" yonger than "+ upperlimit, data = obj)
                lines.append(line)
            elif age <= 50:
                line, =plt.plot('date', 'value', color='orange', label=status+" yonger than "+ upperlimit, data = obj)
                lines.append(line)
            elif age <= 75:
                line, =plt.plot('date', 'value', color='purple', label=status+" yonger than "+ upperlimit, data = obj)
                lines.append(line)
            else:
                line, =plt.plot('date', 'value', color='pink', label=status+" yonger than "+ upperlimit, data = obj)
                lines.append(line)
        plt.legend(handles = lines)
            
    fig.autofmt_xdate()  # To show dates nicely
    regionName = input_data["region"]["name"]
    plt.title('Confirmed cases in '+ regionName)
    plt.xlabel("dates")
    plt.ylabel("# cases")
    if save:
        if sex:
            plt.savefig(regionName + '_evolution_cases_sex.png')
        else:
            plt.savefig(regionName + '_evolution_cases_age.png')
    plt.show()

def compute_running_average(data, window):
    if window % 2 == 0:
        raise ValueError("window should be odd")
    if window == 1:
        return data
    result = []
    step = int((window-1)/2)
    for i in range(len(data)):
        if step > i or step + i >= len(data): # beyond the range
            result.append(None)
        else:
            sum = 0
            for j in range(i-1, i-step-1, -1):
                sum+=data[j]
            for k in range(i +1, i + step+1):
                sum+=data[k]
            if data[i] is not None:
                sum+=data[i]
            else:
                window-=1
            average = sum/window
            result.append(average)
    return result
    

def simple_derivative(data):
    result = []
    result.append(None)
    for i in range(1, len(data)):
        if data[i] is None or data[i-1] is None:
            result.append(None)
        else:
            result.append(data[i] - data[i-1])
    return result



def count_high_rain_low_tests_days(input_data):
    dates = input_data["evolution"]
    rainfallList = []
    testList = []
    for date in dates.keys():
        rainfallList.append(dates[date]["weather"]["rainfall"])
        testList.append(dates[date]["epidemiology"]["tested"]["new"]["all"])
    
    smoothTestList = compute_running_average(testList, 7)

    derivativeTest = simple_derivative(smoothTestList)
    derivativeRainfull = simple_derivative(rainfallList)

    totalRainIncreased = 0
    for i in derivativeRainfull:
        if i is not None and i > 0:
            totalRainIncreased += 1

    totalObservedDay = 0
    for i in range(len(dates.keys())):
        if derivativeTest[i] is not None and derivativeRainfull[i] is not None \
            and derivativeRainfull[i] > 0 and derivativeTest[i] < 0:
            totalObservedDay += 1
    
    return totalObservedDay / totalRainIncreased