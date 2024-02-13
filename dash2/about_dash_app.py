from dash import Dash, dash_table
import pandas as pd
import dash_design_kit as ddk

df = pd.read_csv('https://git.io/Juf1t')

app = Dash(__name__)

app.layout = ddk.App(show_editor=True, children=[
    ddk.DataTable(
       id='table',
       columns=[{"name": i, "id": i} for i in df.columns],
       data=df.to_dict('records'),
       editable=True
   )
])

if __name__ == '__main__':
    app.run(debug=True)