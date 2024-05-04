from dash import html, dcc
import dash_bootstrap_components as dbc

predictions = html.Div( children=[
            
        dbc.Row([
            dbc.Col(class_name="descripition_sarima"), 
            
            dbc.Col(class_name="graph_prediction")
        ]),
        
        dbc.Row([
            dbc.Col(class_name="graph_autocorrelation"),
            
            dbc.Col(class_name="graph_partial_autocorrelation")
        ])                   
                           
                           
], className="predict_container")