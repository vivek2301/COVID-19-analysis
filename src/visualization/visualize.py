import pandas as pd
import numpy as np
import sys
sys.path.append("..")

from data.get_data import get_johns_hopkins
from data.process_JH_data import store_relational_JH_data
from features.build_features import build_JH_features
from models.sir_model import sir_modelling

import dash
dash.__version__
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output,State

import plotly.graph_objects as go

import os

df_input_large=pd.read_csv('../../data/processed/COVID_final_set.csv',sep=';')


fig1 = go.Figure()
fig2 = go.Figure()

app = dash.Dash()
app.layout = html.Div([

    dcc.Markdown('''
    #  Applied Data Science on COVID-19 data

    Goal of the project is to teach data science by applying a cross industry standard process,
    it covers the full walkthrough of: automated data gathering, data transformations,
    filtering and machine learning to approximating the doubling time, and
    (static) deployment of responsive dashboard.

    '''),

    dcc.Tabs(id='tabs', value='visualization_tab', children=[
        dcc.Tab(label='Visualization', value='visualization_tab', children=[

            dcc.Markdown('''
            ## Multi-Select Country for visualization
            '''),


            dcc.Dropdown(
                id='country_list_drop_down',
                options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
                value=['US', 'Germany','Italy'], # which are pre-selected
                multi=True
            ),

            dcc.Markdown('''
                ## Select Timeline of confirmed COVID-19 cases or the approximated doubling time
                '''),


            dcc.Dropdown(
            id='doubling_time',
            options=[
                {'label': 'Timeline Confirmed ', 'value': 'confirmed'},
                {'label': 'Timeline Confirmed Filtered', 'value': 'confirmed_filtered'},
                {'label': 'Timeline Doubling Rate', 'value': 'confirmed_DR'},
                {'label': 'Timeline Doubling Rate Filtered', 'value': 'confirmed_filtered_DR'},
            ],
            value='confirmed',
            multi=False
            ),

            dcc.Graph(figure=fig1, id='visualization_graph')
        ]),

        dcc.Tab(label='SIR modelling', value='SIR_tab', children=[
            dcc.Markdown('''
            ## Select Country for SIR modelling
            '''),


            dcc.Dropdown(
                id='country_drop_down',
                options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
                value='US', # Pre-selected country
                multi=False
            ),

            dcc.Graph(figure=fig2, id='SIR_graph')
        ])
    ])
])



@app.callback(
    Output('visualization_graph', 'figure'),
    [Input('country_list_drop_down', 'value'),
    Input('doubling_time', 'value')])
def update_visualization(country_list,show_doubling):

    if 'doubling_rate' in show_doubling:
        my_yaxis={'type':"log",
               'title':'Approximated doubling rate over 3 days (larger numbers are better #stayathome)'
              }
    else:
        my_yaxis={'type':"log",
                  'title':'Confirmed infected people (source johns hopkins csse, log-scale)'
              }

    traces = []
    for each in country_list:

        df_plot=df_input_large[df_input_large['country']==each]

        if show_doubling=='doubling_rate_filtered':
            df_plot=df_plot[['state','country','confirmed','confirmed_filtered','confirmed_DR','confirmed_filtered_DR','date']].groupby(['country','date']).agg(np.mean).reset_index()
        else:
            df_plot=df_plot[['state','country','confirmed','confirmed_filtered','confirmed_DR','confirmed_filtered_DR','date']].groupby(['country','date']).agg(np.sum).reset_index()

        traces.append(dict(x=df_plot.date,
                                y=df_plot[show_doubling],
                                mode='markers+lines',
                                opacity=0.9,
                                name=each
                        )
                )

    return {
            'data': traces,
            'layout': dict (
                width=1280,
                height=720,

                xaxis={'title':'Timeline',
                        'tickangle':-45,
                        'nticks':20,
                        'tickfont':dict(size=14,color="#7f7f7f"),
                      },

                yaxis=my_yaxis
        )
    }

@app.callback(
    Output('SIR_graph', 'figure'),
    [Input('country_drop_down', 'value')])
def update_sir(country):

    traces = []
    
    df_plot=df_input_large[df_input_large['country']==country]
    df_plot=df_plot[['state','country','confirmed','date']].groupby(['country','date']).agg(np.sum).reset_index()
    df_plot.sort_values('date',ascending=True).head()
    df_plot = df_plot.confirmed[60:]

    t, fitted = sir_modelling(df_plot)

    traces.append(dict(x=t,
                        y=fitted,
                        mode='markers',
                        opacity=0.9,
                        name='SIR fit'
                    )
            )
    
    traces.append(dict(x=t,
                        y=df_plot,
                        mode='lines',
                        opacity=0.9,
                        name='True data'
                    )
            )

    return {
            'data': traces,
            'layout': dict (
                width=1280,
                height=720,
                title='Fit of SIR model',

                xaxis={'title':'Days',
                        'tickangle':-45,
                        'nticks':20,
                        'tickfont':dict(size=14,color="#7f7f7f"),
                      },

                yaxis={'title':"Population infected"
                      }
        )
    }

def update_data():
    # Pull and load the latest data
    # First git clone needed for Johns Hopkins data - https://github.com/CSSEGISandData/COVID-19.git
    get_johns_hopkins()
    store_relational_JH_data()
    build_JH_features()

if __name__ == '__main__':
    #update_data()
    app.run_server(debug=True, use_reloader=False)
