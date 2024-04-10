import pandas as pd
from .dash_figures import *

df_map_volatile = df

selected_areas = []
month_filter = pd.to_datetime(df2['datetime']).dt.strftime('%B').unique().tolist()
month_filter.append("Diario")    

actual_val = "pm_25_mean"
actual_month = "Diario"
actual_month_reg = "Diario"


def get_areas_border(df, selected_areas):
    
    feature_areas = {'op': [], 'wid': [], 'col': []}

    for display_name in df.neighborhood.items():
        if display_name[1] in selected_areas:
            feature_areas['op'].append(1)
            feature_areas['wid'].append(3)
            feature_areas['col'].append('red')
        else:
            feature_areas['op'].append(0.50)
            feature_areas['wid'].append(1)
            feature_areas['col'].append('black')

    
    return feature_areas


def get_month_data(df, df2, datetime):   
    df_map_volatile = pd.DataFrame()
    if datetime != "Diario":
        df2['datetime'] = pd.to_datetime(df2['datetime'])
        selected_month_data = df2[(df2['datetime'].dt.strftime('%B') == datetime) & (df2['neighborhood'] != 'Unknown Zone')]           
        df_map_volatile = selected_month_data.groupby('neighborhood').agg(
            pm_25_mean=('pm_25', 'mean'),
            pm_10_mean=('pm_10', 'mean'),
            temperature_mean=('temperature', 'mean'),
            humidity_mean=('humidity', 'mean')
        ).reset_index()     
    else:
        df_map_volatile = df  
    return df_map_volatile

# ******************** Regression ******************


def create_time_series(datetime):
    
    global selected_areas, df2, df3, actual_month_reg, actual_val, actual_month
    
    df3 = pd.DataFrame(columns=['id_rute','datetime','pm_25','pm_10','temperature','humidity','neighborhood', 'name'])
 
    for selected_neigh in selected_areas:
             
        filter_neigh = df2.loc[df2['neighborhood'] == selected_neigh]
        
        filter_neigh['name'] = filter_neigh['neighborhood'].str.split(',').str[0]
                                
        df3 = pd.concat([df3, filter_neigh], ignore_index=True)

    df3.sort_values(by='datetime', inplace=True) 
    
    if actual_month_reg != datetime:
        if datetime != "Diario":
            actual_month_reg = datetime
            df_aux = df3.copy()
            df_aux['datetime'] = pd.to_datetime(df_aux['datetime'])
            df_aux = df_aux[(df3['datetime'].dt.strftime('%B') == datetime) & (df3['neighborhood'] != 'Unknown Zone')]
            return df_aux
        else:
            return df3
        
    return df3  

def create_bar_graph():
    global selected_areas, df
    df_bar = pd.DataFrame({
        'neighborhood': [],
        'variable': [],
        'value': []
    })

    for area in selected_areas:
        filtered_df = df[df['neighborhood'] == area]
        filtered_df['neighborhood'] = filtered_df['neighborhood'].str.split(',').str[0]
        filtered_df = filtered_df.melt(id_vars=['neighborhood'], value_vars=['pm_25_mean', 'pm_10_mean', 'humidity_mean', 'temperature_mean'])
        filtered_df.columns = ['neighborhood', 'variable', 'value']
        df_bar = pd.concat([df_bar, filtered_df], ignore_index=True)
        
    return df_bar