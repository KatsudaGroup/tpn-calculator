import pandas as pd
import re

def calc_signal_sum(df: pd.DataFrame, mw_column_name: str = 'kDa'):
    ret = {}
    for column in df.columns:
        if column == mw_column_name:
            continue
        signal_sum = df[column].sum()
        ret[column] = signal_sum
    return ret

def calc_signal_sum2(df: pd.DataFrame, mw_column_name: str = 'kDa'):
    ret = {}
    sorted_df = df.sort_values(by = mw_column_name, ascending = False).reset_index(drop = True)
    for column in sorted_df.columns:
        if column == mw_column_name:
            continue
        signal_sum = sorted_df[column].sum()
        ret[column] = signal_sum
    return ret

def calc_signal_sum_positive_region(df: pd.DataFrame, mw_column_name: str = 'kDa'):
    ret = {}
    sorted_df = df.sort_values(by = mw_column_name, ascending = False).reset_index(drop = True)
    for column in sorted_df.columns:
        if column == mw_column_name:
            continue
        negative_indices = sorted_df[sorted_df[column] < 0.0].index
        if not negative_indices.empty:
            stop_index = negative_indices[0]
        else:
            stop_index = len(sorted_df[column])
        #print("{}: {} {}".format(column, stop_index, sorted_df[mw_column_name][0:stop_index]))
        signal_sum = sorted_df[column][0:stop_index].sum()
        ret[column] = signal_sum
    return ret


def expand_range(input_str):
    result = []
    if input_str == None or isinstance(input_str, str) != True:
        return None

    # Only interger, ',', '-' are allowed.
    if not re.fullmatch(r"[0-9,\-]+", input_str):
        return None
    
    parts = input_str.split(',')
    for part in parts:
        part = part.strip() 
        if len(part) == 0:
            continue
        if part == "": 
            return None
        if part.count('-') > 1:
            return None
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError(f"Invalid value: {start}-{end}")
                result.extend(range(start, end + 1))
            except ValueError as ve:
                return None
        else:
            try:
                result.append(int(part))
            except ValueError:
                return None
    return result

def parse_labeled_numbers(input_str):
    # Pattern: number (integer or float) with optional label in [label] (label must not contain [ or ])
    pattern = r'\s*(\d+(?:\.\d+)?)(?:\[([^\[\]]*)\])?\s*'

    parts = input_str.split(',')
    result = []

    for part in parts:
        match = re.fullmatch(pattern, part)
        if not match:
            raise ValueError(f"Invalid element: '{part}'")

        number_str = match.group(1)
        label = match.group(2) if match.group(2) else None
        number = float(number_str) if '.' in number_str else int(number_str)

        result.append((number, label))

    return result
