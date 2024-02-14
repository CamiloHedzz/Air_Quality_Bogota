from dash import Dash, dash_table
import pandas as pd
from django_plotly_dash import DjangoDash

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')

app = DjangoDash('dash_table')

app.layout = dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns])

if __name__ == '__main__':
    app.run(debug=True)