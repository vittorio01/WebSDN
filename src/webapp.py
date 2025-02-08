import dash
import dash_cytoscape as cyto
from dash import html, Input, Output, callback
import dash_ag_grid as dag
import dash_draggable as draggable

import requests  # Per recuperare la topologia SDN
from NetworkDescription import *

app = dash.Dash(__name__,external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"])

nodes = [{"data": {"id": "1", "label": "Switch 1"}},
         {"data": {"id": "2", "label": "Switch 2"}},
         {"data": {"id": "3", "label": "Host A"}}]
edges = [{"data": {"source": "1", "target": "2"}},
         {"data": {"source": "1", "target": "3"}}]

deviceListColumnDefs = [
    { 'field': 'Link' },
    { 'field': 'Device ' },
    { 'field': 'Connected with'},
]
deviceDetailsColumnDefs= [
    { 'field': 'Details' },
]

rowDefs = [
    { 'field': 'direction' },
    { 'field': 'strength' },
    { 'field': 'frequency'},
]


app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                dag.AgGrid(
                    id="deviceListGrid",
                    columnSize="sizeToFit",
                    rowData=rowDefs,
                    columnDefs=deviceListColumnDefs,
                    style={"width":"100%","height":"100%"}
                ),
            ],id="deviceListDiv"),
            html.Div([],id="hBar"),
            html.Div([
                dag.AgGrid(
                    id="deviceDetailsGrid",
                    columnSize="sizeToFit",
                    rowData=rowDefs,
                    columnDefs=deviceDetailsColumnDefs,
                    style={"width":"100%","height":"100%"}
                ),
            ],id="deviceDetailsDiv"),
        ],id="detailsDiv"),
        html.Div([],id="vBar"),
        html.Div([
            html.Div([
                html.Button([
                    html.I(className="fa-solid fa-arrow-left", id="fullscreenIcon")
                ], id="fullscreenButton", n_clicks=0),
                html.H1("SDN Network Layout",id="topBarText"),
            ],id="topBarDiv"), 
            html.Div([
                cyto.Cytoscape(
                id="topology",
                style={"width":"100%","height":"100%"},
                elements=nodes + edges,
                layout={'name': 'circle'},
                stylesheet=[
                    {"selector": 'node', "style": {"content": "data(label)", "background-color": "#0074D9"}},
                    {"selector": 'edge', "style": {"line-color": "#FF4136"}}
                    ])
            ],id="topologyDiv"), 
        ],id="rightDiv"), 
    ],id="contentsDiv")
],id="pageDiv")

if __name__ == '__main__':
    app.run_server(debug=True)