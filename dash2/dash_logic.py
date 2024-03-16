import pandas as pd

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