import pandas as pd
from styleframe import StyleFrame, Styler, utils
import os
import src.colorLog as log
def write(df, dict_tmp, columns):
    if df.empty==True:
        df= creat_df(columns = columns)
    # print(dict_tmp)
    df = df.append(dict_tmp, ignore_index = True)
    log.Logger('\t\t\t\tSHOW TABLE' , "BLUE", "WHITE",timestamp=0)
    log.Logger('%s'%df , "BLUE", "WHITE",timestamp=0)
    return df
def creat_df(columns):
    log.Logger('[SYSTEM MSG] Create dataframe.' , 'BLUE', 'WHITE')
    df = pd.DataFrame(columns = columns)
    print(df)
    return df
def save_to_excel(df,excel_writer,columns):
    
    sf = StyleFrame(df)
    # sf.apply_column_style(cols_to_style=columns, bold=True)

    sf.to_excel(
    excel_writer=excel_writer, 
    best_fit=columns,
    columns_and_rows_to_freeze='a1', 
    row_to_add_filters=0,
    )
    excel_writer.save()
    excel_writer.close()
    log.Logger('[SYSTEM MSG] Dataframe save to excel.' , 'BLUE', 'WHITE')