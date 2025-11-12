import os
import pandas as pd
import string
from typing import Any
import yaml

class Utils:
    '''
    The class for utilities.
    '''

    @classmethod
    def custom_sort_values(cls, s: pd.Series[str], ascending: bool = True) -> pd.Series[str]:
        '''
        Sort values ascending/decending-ly, but keep the lower and upper case variants adjacent to each other.
        '''

        custom_order = {ch: i for i, ch in enumerate(
            sum(([u, l] for u, l in zip(string.ascii_uppercase, string.ascii_lowercase)), [])
        )}

        def custom_sort_key(value: str | float | None):
            if not isinstance(value, str):
                return (float('inf'), value)

            key = []
            for ch in value:
                if ch in custom_order:
                    key.append((0, custom_order[ch]))
                else:
                    key.append((1, ord(ch)))
            
            return key
        
        sorted_series = s.sort_values(
            key = lambda x: x.map(custom_sort_key),
            ascending = ascending,
            ignore_index = True
        )
        return sorted_series

    @classmethod
    def get_type(cls,
                 s: pd.Series) -> str:
        '''
        Retrieve the type of the series.
        '''

        if s.empty:
            return '<class \'empty\'>'
        
        if s.dtype != 'object':
            return str(s.dtype)
        
        types: pd.Series[int] = s.apply(type).value_counts()    # type: ignore
        if len(types) == 1:
            return str(types.index[0])
        else:
            return '<class \'mixed\'>'

    @classmethod
    def normalize_value(cls, value, case_sensitive: bool = False) -> str:
        '''
        Normalize values to strings.
        '''

        if value is None:
            return ''
        
        if not isinstance(value, (list, set, tuple)):
            try:
                if pd.isna(value):
                    return ''
            except Exception:
                pass
        
        if isinstance(value, (list, set, tuple)):
            value = '<SEP>'.join(map(str, value))

        elif not isinstance(value, str):
            value = str(value)

        value = value.replace(' ', '').replace('<SEP>', ' ')

        if not case_sensitive:
            value = value.lower()
        
        return value


    @classmethod
    def read_yaml(cls,
                  path: str | bytes | os.PathLike[str]) -> Any:
        '''
        Read the YAML file.
        '''

        with open(path, 'r', encoding = 'utf-8') as f:
            yaml_file = yaml.safe_load(f)

        return yaml_file