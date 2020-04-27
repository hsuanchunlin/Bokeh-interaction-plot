#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 22:58:09 2020

@author: fatmimi
"""

import geopandas as gp
import glob

import pandas as pd

# convert data to json
import json
from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.models import Slider, HoverTool
from bokeh.layouts import widgetbox, row, column
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, HoverTool, Slider
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column

shp_file_ = glob.glob("./tl_2016_us_county/*.shp")
csv_file_ = glob.glob("*.csv")
print("SHP:", shp_file_)
print("CSV:", csv_file_)

all_state = pd.read_csv(csv_file_[0])
all_state = all_state.fillna(0)
gdf = gp.read_file(shp_file_[0])

florida_geo = gdf[gdf.STATEFP.astype(int) == 12]
county_list = all_state.county.unique()

#Now we can have a loop to summarize the counties in only florida
florida_df = all_state[all_state.state == "Florida"]
fips_ = florida_df.fips.unique()
date_list = florida_df.date.unique()
converted_list = []
for fips in fips_:
    temp_01 = florida_df.groupby('fips').get_group(fips).T
    temp_01.columns = temp_01.loc['date']
    temp_01 = temp_01.drop(['date', 'county', 'state', 'fips', 'deaths'], axis = 0)
    temp_01.insert(0,"GEOID",fips)
    converted_list.append(temp_01)
#Convert to the final df

case_df = pd.concat(converted_list, axis = 0)
case_df = case_df.fillna(0)

case_df.GEOID = case_df.GEOID.astype('float')
florida_geo.GEOID = florida_geo.GEOID.astype('float')
merge_fl_test= florida_geo.merge(case_df[["GEOID",date_list[-1]]], on = "GEOID", how = 'left')
merge_fl_test = merge_fl_test.rename(columns={date_list[-1]:'cases'})
json_data = json.loads(merge_fl_test.to_json())
json_data = json.dumps(json_data)

#Input the jason data for initiative plotting
geosource = GeoJSONDataSource(geojson = json_data)

#Define function that returns json_data for year selected by user.
#Make a slider object: slider 
date_length = len(date_list)
slider = Slider(title = 'date',start = 0, end = date_length, step = 1, value = date_length)
slider.on_change('value', update_plot)

def json_data(selectedDate):
    date = date_list[selectedDate]
    merge_fl_test= florida_geo.merge(case_df[["GEOID",date]], on = "GEOID", how = 'left')
    merge_fl_test = merge_fl_test.rename(columns={date:'cases'})
    json_data = json.loads(merge_fl_test.to_json())
    json_data = json.dumps(json_data)
    return json_data

def update_plot(attr, old, new):
    date = slider.value
    new_data = json_data(date)
    geosource.geojson = new_data
    p.title.text = 'Confirmed cases in Florida, %d' %date
    
#

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][8]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 300)

#Define custom tick labels for color bar.
#tick_labels = {'0': '0%', '5': '5%', '10':'10%', '15':'15%', '20':'20%', '25':'25%', '30':'30%','35':'35%', '40': '>40%'}

#Create color bar. 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
border_line_color=None,location = (0,0), orientation = 'horizontal'
                     #, major_label_overrides = tick_labels
                    )

#Add hover tool
hover = HoverTool(tooltips = [ ('Country','@NAME'),('Cases', '@cases')])

#Create figure object.
p = figure(title = 'Cases for last update', plot_height = 500, plot_width = 500, toolbar_location = None,
           tools = [hover])
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

#Add patch renderer to figure. 
p.patches('xs','ys', source = geosource,
          fill_color = {'field' :'cases', 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)


#Specify figure layout.
p.add_layout(color_bar, 'below')
# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(p,widgetbox(slider))
curdoc().add_root(layout)

#Display figure.
show(layout)