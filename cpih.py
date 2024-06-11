import math
from datetime import date,datetime
from babel.numbers import format_currency
from ons_api import *


def string_to_datetime(row):
    datetime_object = datetime.strptime(row['id'], '%b-%y')
    return datetime_object


def generate_list_of_year_months(start_year, salary_increase_month, latest_date):
    year_months = []

    current_date = date.today()
    current_year = current_date.year
    current_month = current_date.month

    looping_year = start_year
    while looping_year < current_year:
        year_months.append(datetime.strptime(salary_increase_month + str(looping_year), '%b%Y'))
        looping_year += 1
    # TODO - refactor due to repetition
    temp = datetime.strptime(salary_increase_month + str(looping_year), '%b%Y')
    if latest_date.month < temp.month:
        year_months.append(latest_date)
    else:
        year_months.append(temp)

    return year_months


def get_cpih():
    dataset_name = "Consumer Prices Index including owner occupiers' housing costs (CPIH)"
    cpih_dimensions = {
        "aggregate": "CP00",
    }
    cpih = get_timeseries(dataset_name, cpih_dimensions)[0]

    # TODO - we may find we want to do this same thing for other ONS data, if so need to pull it out into a generic method
    # here we sort and reindex the data by date
    cpih['id'] = cpih.apply(string_to_datetime, axis=1)
    cpih = cpih.sort_values("id")
    cpih.reset_index(drop=True, inplace=True)

    return cpih


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def match_salary_to_inflation_over_time(starting_salary, starting_year, salary_increase_month):
    # TODO - should get this all into a class and then get_cpih() once globally
    cpih = get_cpih()

    latest_date = cpih['id'].iloc[-1]
    # TODO - fix type
    latest_date.date()
    #print(type(latest_date))

    cpih['percentage'] = cpih['observation'].astype(float).pct_change(periods=12).fillna(0)

    my_list = generate_list_of_year_months(starting_year, salary_increase_month, latest_date)
    results = cpih.loc[cpih["id"].isin(my_list)]

    results.reset_index(drop=True, inplace=True)
    results = results.assign(inflation_matching_salary = starting_salary)
    for i in range(len(results.percentage) - 1):
        results.loc[i+1, 'inflation_matching_salary'] = results.loc[i, 'inflation_matching_salary'] * (1 + results.loc[i+1, 'percentage'])
    print(results)

    # TODO might need to change this into a sperate method
    if latest_date.date() < date.today():
        # then the last line is what our next pay should be
        # in which case we need to get the line before for our current pay
        next_pay = results['inflation_matching_salary'].iloc[-1]
        current_pay = results['inflation_matching_salary'].iloc[-2]
    else:
        # the last line will show what our current pay should be
        # in which case we need to calulate what our next pay should be, which involves getting the latest cpih figure
        current_pay = results['inflation_matching_salary'].iloc[-1]
        next_pay = current_pay * (1 + cpih['percentage'].iloc[-1])

    return results, next_pay, current_pay


def main():
    results, next_pay, current_pay = match_salary_to_inflation_over_time(96000.0, 2018, 'Jul')
    print("\n")
    print(f"Average inflation was: {results.loc[:, 'percentage'].mean()}")
    print(f"Your current salary should be: {format_currency(current_pay, 'GBP', locale='en_GB')}")
    print(f"Your next salary should be: {format_currency(next_pay, 'GBP', locale='en_GB')}")

    print("\n")
    cpih = get_cpih()
    old_date = datetime(2003, 1, 1)
    latest_date = cpih['id'].iloc[-1]
    data = cpih.loc[cpih["id"].isin([old_date, latest_date])]
    print(data)
    # since Jan 2003
    average_yearly_inflation = (12 / diff_month(latest_date,old_date)) * ((float(data['observation'].iloc[1]) / float(data['observation'].iloc[0])) - 1)
    print(f"\nAvg yearly inflation since 2003 (over {diff_month(latest_date,old_date)} months): {average_yearly_inflation}")

if __name__ == "__main__":
    main()
