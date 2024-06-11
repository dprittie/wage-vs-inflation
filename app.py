import altair as alt
import streamlit as st
import pandas as pd
import datetime
from cpih import *

header = st.container()
inputs = st.container()
graphs = st.container()

with header:
    st.title("Has your salary kept up with inflation over time?")
    #st.text("Also Zig Bub is here")

with inputs:

    # TODO in an ideal world I would get 1989 as the oldest year from the ons cpih data
    THIS_YEAR = datetime.today().year
    YEARS = list(range((THIS_YEAR -1), 1989, -1))
    starting_year = st.selectbox(
       "Start year for salary analysis",
       (YEARS),
       placeholder="Select start year...",
    )

    # TODO generate the month list from the datetime lib
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    salary_increase_month = st.selectbox(
       "The first month your new salary gets paid after a pay rise",
       (MONTHS),
       placeholder="Select pay rise month...",
    )

    # below we enter our salary from each year until this year
    # we have to have an input for starting salary but every year afterwards is optional except current salary
    # if we dont know interim salaries we assume a steady rise in pay from starting year to now
    salaries_over_time = pd.DataFrame(columns=['actual_salary'])
    #if 'salaries_over_time' not in st.session_state:
    #    st.session_state.salaries_over_time = salaries_over_time
    st.session_state.salaries_over_time = salaries_over_time

    # TODO - we need to check the month here, if we are < salary increase month then we do not show the current year
    input_values = [st.number_input(f'Salary for year: {i}', 0, key=f"text_input_{i}")
        for i in list(range(starting_year, THIS_YEAR + 1))]
    starting_salary = input_values[0]

    if st.button("Save salary history", key="button_update"):
        # Update dataframe state
        st.session_state.salaries_over_time = pd.concat(
            [st.session_state.salaries_over_time, pd.DataFrame({'actual_salary': input_values})],
            ignore_index=True)
        st.text("Updated dataframe")

    #"## Dataframe state:"
    #st.dataframe(st.session_state.salaries_over_time)

    results, next_pay, current_pay = match_salary_to_inflation_over_time(starting_salary, starting_year, salary_increase_month)
    results.drop(columns=['observation', 'percentage'])
    salary_compare = pd.concat([st.session_state.salaries_over_time, results], axis=1)

with graphs:
    domain = ['actual_salary', 'inflation_matching_salary']
    range_ = ['green', 'red']

    ch = alt.Chart(salary_compare.reset_index()).transform_fold(['actual_salary', 'inflation_matching_salary']).mark_line().encode(
        alt.X('id:T'),
        alt.Y('value:Q').scale(zero=False),
        color=alt.Color('key:N', scale=alt.Scale(domain=domain, range=range_)),
    )
    st.altair_chart(ch, use_container_width=True)
