
from django_plotly_dash import DjangoDash
from dash import Output, Input, State
from dash import html, dash_table

app = DjangoDash('SimpleExample2', external_stylesheets=['dash2\static\dash_style.css'])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

df3 = []

app.layout = html.Div([
    
    html.Button('Obtener Resultados', id='add-row-button', n_clicks=0,
                style={'backgroundColor': '#DBD22A', 'border': 'none', 'color': 'white', 'padding': '15px 32px', 'text-align': 'center', 'text-decoration': 'none', 'display': 'inline-block', 'font-size': '16px', 'margin': '4px 2px', 'cursor': 'pointer', 'border-radius': '10px'}),
    
    html.H3("Máximo valor de partículas PM 2.5 en barrios seleccionados",
            style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontSize': '18px', 'marginBottom': '20px', 'borderBottom':'solid 2px #DBD22A'}),
    dash_table.DataTable(
        id='table-max-pm',
        columns=[
            {"name": "Identificacion Barrio", "id": "code"},
            {"name": "Valor PM 2.5 µg/m³", "id": "sampl"},
            {"name": "Hora", "id": "value"}
        ],
        data=df3,
        style_table={'overflowX': 'auto'},
        style_cell={'border': 'none', 'fontSize': '16px','fontFamily': 'Oswald Light','textAlign': 'left', 'backgroundColor': '#F2F2F2'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#F2F2F2'}
    ),

    html.H3("Minimo valor de particulas PM 2.5 en barrios seleccionados",
            style={'fontFamily': 'Oswald Light', 'textAlign': 'justify', 'fontSize': '18px', 'marginBottom': '20px', 'borderBottom':'solid 2px #DBD22A'}),
    dash_table.DataTable(
        id='table-min-pm',
        columns=[
            {"name": "Identificacion Barrio", "id": "code"},
            {"name": "Valor PM 2.5 µg/m³", "id": "sampl"},
            {"name": "Hora", "id": "value"}
        ],
        data=df3,
        style_table={'overflowX': 'auto'},
        style_cell={'border': 'none', 'fontSize': '16px','fontFamily': 'Oswald Light','textAlign': 'left', 'backgroundColor': '#F2F2F2'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#F2F2F2'}
    ),
])

@app.callback(
    Output('table-max-pm', 'data'),
    Output('table-min-pm', 'data'),
    [Input('add-row-button', 'n_clicks')],
    [State('table-max-pm', 'data'),
     State('table-min-pm', 'data')]
)
def update_tables(n_clicks, max_pm_data, min_pm_data):  
    df3 = get_data_df3()
    
    if n_clicks > 0:
        main_data_mx = df3.loc[df3['sampl'] == df3['sampl'].max()]
        main_data_mn = df3.loc[df3['sampl'] == df3['sampl'].min()]

        max_pm_data = []
        min_pm_data = []
        
        for i, value in main_data_mx.iterrows():
            max_pm_data.append({
                "code": value['code'],
                "sampl": value['sampl'],
                "value": value['datetime'].strftime('%H:%M:%S')
            })
        
        for i, value in main_data_mn.iterrows():
            min_pm_data.append({
                "code": value['code'],
                "sampl": value['sampl'],
                "value": value['datetime'].strftime('%H:%M:%S')
        })

    return max_pm_data, min_pm_data

def get_data_df3():
    from .dash_app import df3
    return df3

if __name__ == '__main__':
    app.run_server(debug=True)