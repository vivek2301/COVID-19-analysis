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

print(os.getcwd())
df_input_large=pd.read_csv('../../data/processed/COVID_final_set.csv',sep=';')


fig = go.Figure()

app = dash.Dash()
app.layout = html.Div([

    dcc.Markdown('''
    #  Applied Data Science on COVID-19 data

    Goal of the project is to teach data science by applying a cross industry standard process,
    it covers the full walkthrough of: automated data gathering, data transformations,
    filtering and machine learning to approximating the doubling time, and
    (static) deployment of responsive dashboard.

    '''),

    dcc.Markdown('''
    ## Select Country for SIR modelling
    '''),


    dcc.Dropdown(
        id='country_drop_down',
        options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
        value='Germany', # Pre-selected country
        multi=False
    ),

    dcc.Graph(figure=fig, id='main_window_slope')
])



@app.callback(
    Output('main_window_slope', 'figure'),
    [Input('country_drop_down', 'value')])
def update_figure(country):

    traces = []
    
    df_plot=df_input_large[df_input_large['country']==country]
    df_plot=df_plot[['state','country','confirmed','date']].groupby(['country','date']).agg(np.sum).reset_index()
    df_plot.sort_values('date',ascending=True).head()
    df_plot = df_plot.confirmed[35:]

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

if __name__ == '__main__':
    # Pull and load the latest data
    get_johns_hopkins()
    store_relational_JH_data()
    build_JH_features()

    app.run_server(debug=True, use_reloader=False)
