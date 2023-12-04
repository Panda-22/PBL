# streamlit run app.py

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import datetime
import requests
import json

# loading datasets
data = pd.read_csv('master.csv', thousands = ',', encoding = 'utf-8')

# setting interface
st.markdown("<div style = 'background: #e6e6e6'><h3 style = 'font-weight:bold; color: #ac2217'><center>Facts of Suicides</center></h3><div>", unsafe_allow_html = True)
st.markdown("<center> </center>", unsafe_allow_html = True)
st.sidebar.expander('')
st.sidebar.subheader('Select year, country, gender, age:') 

#***** 1-World Altas *****
# by year
start_time = st.sidebar.slider('1 - Select year:', 
                    data['year'].min(),
                    data['year'].max(),
                    1990)
year_data = data.loc[data['year'] == start_time]
country_lst = ['All countries'] + list(data['country'].unique())
country  = st.sidebar.selectbox('2 - Select country', (country_lst), key = "country")

# mapping the year data on world altas

url = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json'
world_map = alt.topo_feature(url,"countries")

# stats for total number of suicides
year_data_sum = year_data.groupby('country', as_index=False).agg({'suicides_no':'sum'})

mapping_total = alt.Chart(world_map).mark_geoshape().encode(
    color = alt.Color(field = 'suicides_no', type = "quantitative",
                                    scale = alt.Scale(),
                                    legend = alt.Legend(title = 'Suicides')),
        tooltip = ['country:N', 'suicides_no:Q']
        ).transform_lookup(lookup = "properties.name",
            from_ = alt.LookupData(year_data_sum, 'country',  list(year_data_sum.columns)
            )).project(type='mercator'
                ).properties(width = 650, height = 450, 
                title = 'Suicide stats for %s in %s: total number of suicides' %(country, start_time))

st.altair_chart(mapping_total)

# stats for suicides per 100k population
year_data_per = year_data.groupby('country', as_index=False).agg({'suicides/100k pop':'sum'})

if country == 'All countries':
    year_data_country = year_data_per
    country_data = data
else:
    year_data_country = year_data_per.loc[year_data_sum['country'] == country]
    country_data = data.loc[data['country']==country]

mapping_per = alt.Chart(world_map).mark_geoshape().encode(
    color = alt.Color(field = 'suicides/100k pop', type = "quantitative",
                                    scale = alt.Scale(),
                                    legend = alt.Legend(title = 'Suicides')),
        tooltip = ['country:N', 'suicides/100k pop:Q']
        ).transform_lookup(lookup = "properties.name",
            from_ = alt.LookupData(year_data_country, 'country',  list(year_data_country.columns)
            )).project(type='mercator'
                ).properties(width = 650, height = 450, 
                title = 'Suicide stats for %s in %s: suicides per 100k population' %(country, start_time))

st.altair_chart(mapping_per)

#***** 2 - Curved Lines by Country*****

# interface in sidebar
gender_lst = ['All genders', 'female', 'male']
gender = st.sidebar.radio('3 - Select gender:', (gender_lst), key = "sex") 

gender_data_sum= country_data.groupby(['year', 'sex'], as_index=False).agg({'suicides/100k pop':'sum'})

if gender == 'All genders':
    country_data_gender = gender_data_sum
else:
    country_data_gender = gender_data_sum[gender_data_sum['sex'] == gender]

hover = alt.selection(type = 'single', on = 'mouseover', fields = ['sex'], nearest = True)

# base chart
base_chart = alt.Chart(country_data_gender).encode(
   x="year:N",
   y="suicides/100k pop:Q",
   color=alt.condition(hover, "sex:N", alt.value('darkgray')),
        ).add_params(hover
        ).properties(height=300, width=700, 
            title = 'Suicide stats by gender in %s:' %(country)
        ).interactive()

point = base_chart.mark_point(size=2000).encode(
    opacity = alt.value(0)
).add_selection(hover)

singleline = base_chart.mark_line(point=alt.OverlayMarkDef(color="red")).encode(
    size = alt.condition(~hover, alt.value(0.5), alt.value(3))
)

st.altair_chart(point + singleline)

chart = alt.Chart(country_data_gender).mark_point().encode(
    x='year:N',
    y='suicides/100k pop:Q',
    color='sex:N',
    column='sex:N'
    ).properties(width=300, height=240)
    
st.altair_chart(chart)

#***** 3 - Stacked bar chart by age*****
age_lst = ['All ages', '5-14 years', '15-24 years', '25-34 years','35-54 years', '55-74 years', '75+ years']
age  = st.sidebar.selectbox('4 - Select age:', (age_lst), key = 'age')
age_data_sum = country_data.groupby(['year', 'age'], as_index=False).agg({'suicides/100k pop':'sum'})
age_gender_sum = country_data.groupby(['year', 'age','sex'], as_index=False).agg({'suicides/100k pop':'sum'})

if gender == 'All genders' and age == 'All ages':
    country_data_age = age_data_sum
    stack_chart = alt.Chart(country_data_age).mark_area().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
    dotplot = alt.Chart(country_data_age).mark_circle().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
elif gender =='All genders' and age == age:
    age_sum = age_gender_sum[age_gender_sum['age']==age]
    country_data_gender = age_sum.groupby(['year','sex'], as_index=False).agg({'suicides/100k pop':'sum'})
    stack_chart = alt.Chart(country_data_gender).mark_area().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'sex:N',
        tooltip = ['sex:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
    dotplot = alt.Chart(country_data_gender).mark_circle().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'sex:N',
        tooltip = ['sex:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
elif gender == gender and age == 'All ages':
    gender_sum = age_gender_sum[age_gender_sum['sex']==gender]
    country_data_age = gender_sum.groupby(['year','age'], as_index=False).agg({'suicides/100k pop':'sum'})
    stack_chart = alt.Chart(country_data_age).mark_area().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
    dotplot = alt.Chart(country_data_age).mark_circle().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
elif gender != 'All genders' and age != 'All ages':
    country_data_age = age_gender_sum.loc[(age_gender_sum['sex']==gender) &(age_gender_sum['age']==age)]
    stack_chart = alt.Chart(country_data_age).mark_area().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'sex:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
    dotplot = alt.Chart(country_data_age).mark_circle().encode(
        x="year:N",
        y="suicides/100k pop:Q",
        color = 'age:N',
        tooltip = ['age:N', 'sex:N', 'suicides/100k pop:Q']
        ).properties(height=300, width=700, title = 'Suicide stats by age in %s:' %(country)
        ).interactive()
st.altair_chart(stack_chart)
st.altair_chart(dotplot, use_container_width=True) 

#***** 4 - Radial Chart by Country*****
source = year_data_country.loc[year_data_country['suicides/100k pop'] > 250]
base = alt.Chart(source).encode(
    alt.Theta("suicides/100k pop:Q").stack(True),
    alt.Radius("suicides/100k pop").scale(type="sqrt", zero=True, rangeMin=20),
    color="country:N",
    tooltip = ['country:N',  'suicides/100k pop:Q']
).properties(height=420, width=600, title = 'Suicides per 100k population: Top countries')

c1 = base.mark_arc(innerRadius=20, stroke="#fff")
c2 = base.mark_text(radiusOffset=10).encode(text="country:N")
st.altair_chart(c1 + c2)

