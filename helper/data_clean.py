import pandas as pd
import numpy as np


def df_string_to_number(df, col_name, na_replace="0", target_type=np.float):
    if df[col_name].dtype.name != "object":
        return df
    if na_replace != None:
        df[col_name] = df[col_name].fillna(na_replace)
        df[col_name] = df[col_name].apply(lambda x: na_replace if x == "" else x)
    df[col_name] = df[col_name].apply(lambda x: x.replace(",", ""))
    df[col_name] = df[col_name].astype(target_type)
    return df


def df_str_replace(df, col_name, src_str, dst_str=""):
    return df[col_name].apply(lambda x: x.replace(src_str, dst_str))






