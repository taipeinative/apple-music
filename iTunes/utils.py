from __future__ import annotations

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
    def apply_map(cls, df: pd.DataFrame, map_path: str | os.PathLike[str], tmm_path: str | os.PathLike[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
        '''
        Apply the map to unmatched tracks.
        '''

        if isinstance(map_path, str) and not map_path.endswith('yaml'):
            raise ValueError('The `map_path` should point to a YAML file.')
        
        if isinstance(tmm_path, str) and not tmm_path.endswith('csv'):
            raise ValueError('The `tmm_path` should point to a CSV file.')
        
        map_dict: dict[str, object] = cls.read_yaml(map_path)

        if not isinstance(map_dict, dict):
            raise ValueError('The `map_path` should point to a key-value paired YAML file.')
        
        direct_map = map_dict.get('direct', {})
        if not isinstance(direct_map, dict):
            direct_map = {}
        
        fallback_map = map_dict.get('fallback', {})
        if not isinstance(fallback_map, dict):
            fallback_map = {}

        cols = ['ISRC', 'Apple - id']
        tmm_df = pd.read_csv(tmm_path)
        for col in cols:
            if col not in tmm_df.columns:
                raise ValueError(f'The `{col}` column should present in {tmm_path}.')

        df_copy = df.copy()
        df_copy['Matched'] = None
        for index, _ in df_copy.iterrows():
            if not isinstance(index, int):
                continue

            direct = direct_map.get(index)
            if isinstance(direct, int) and (direct in tmm_df.index):
                df_copy.loc[index, 'ISRC'] = tmm_df.loc[direct, 'ISRC']
                df_copy.loc[index, 'Apple ID'] = tmm_df.loc[direct, 'Apple - id']
                df_copy.loc[index, 'Matched'] = tmm_df.loc[direct, 'Track name']
                continue

            fallback = fallback_map.get(index)
            if not isinstance(fallback, dict):
                continue

            isrc = fallback.get('ISRC')
            if isinstance(isrc, str):
                df_copy.loc[index, 'ISRC'] = isrc
            
            apple_id = fallback.get('ID')
            if isinstance(apple_id, int):
                df_copy.loc[index, 'Apple ID'] = apple_id
        
        not_matched = df_copy['ISRC'].isna()
        return df_copy[~not_matched], df_copy[not_matched]

    @classmethod
    def clean_tagged_excel(cls, path: str | os.PathLike[str]) -> pd.DataFrame:
        '''
        Clean the tagged Microsoft Excel file.
        '''

        def to_tuple(row: pd.Series) -> tuple:
            return row['Sub Tag 1'], row['Sub Tag 2'], row['Sub Tag 3']

        if isinstance(path, str) and not path.endswith('xlsx'):
            raise ValueError('The `path` should point to a Microsoft Excel file.')
        
        cols = ['Name', 'Artist', 'Year', 'Play Count', 'Total Time', 'Vocal', 'Language', 'Sub Genres', 'Sub Tag 1', 'Sub Tag 2', 'Sub Tag 3']
        tagged_df = pd.read_excel(path)

        for col in cols:
            if col not in tagged_df.columns:
                raise ValueError(f'The `{col}` column should present in the Microsoft Excel file.')

        tagged_df = tagged_df[cols].rename(columns = {'Sub Genres': 'Genre'})
        tagged_df['Total Time'] = pd.to_timedelta(tagged_df['Total Time'])
        tagged_df['Tags'] = tagged_df.apply(to_tuple, axis = 1)
        tagged_df.drop(columns = ['Sub Tag 1', 'Sub Tag 2', 'Sub Tag 3'], inplace = True)
        return tagged_df

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
    def match_tmm_data(cls,
                       path: str | os.PathLike[str],
                       df: pd.DataFrame,
                       escape_artists: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        '''
        Matches the metadata generated by Tune My Music.
        '''

        if ('Name' not in df.columns) or ('Artist' not in df.columns):
            raise ValueError('The `Name` and `Artist` columns should present in the columns.')

        if isinstance(path, str) and not path.endswith('csv'):
            raise ValueError('The `path` should point to a CSV file.')

        if escape_artists is None:
            escape_artists = []

        def protect_phrases(text):
            mapping = {}
            for i, phrase in enumerate(escape_artists):
                key = f'__ESC_{i}__'
                mapping[key] = phrase
                text = text.replace(phrase, key)
            return text, mapping

        def restore_phrases(parts, mapping):
            out = []
            for p in parts:
                for k, v in mapping.items():
                    p = p.replace(k, v)
                out.append(p)
            return out

        def normalize_artists(text):
            if pd.isna(text):
                return frozenset()
            text, mapping = protect_phrases(text)
            parts = [p.strip().lower() for p in text.split(',') if p.strip()]
            parts = restore_phrases(parts, mapping)
            return frozenset(parts)

        def normalize_artists_tmm(text):
            if pd.isna(text):
                return frozenset()
            text, mapping = protect_phrases(text)
            text = text.replace(' & ', ',')
            parts = [p.strip().lower() for p in text.split(',') if p.strip()]
            parts = restore_phrases(parts, mapping)
            return frozenset(parts)

        def normalize_title(text):
            if pd.isna(text):
                return ''
            return ' '.join(text.lower().split())

        df_copy = df.copy()
        df_copy['_norm_title'] = df_copy['Name'].map(normalize_title)
        df_copy['_norm_artist'] = df_copy['Artist'].map(normalize_artists)

        tmm = pd.read_csv(path).rename(columns = {'Track name': 'Name', 'Artist name': 'Artist'}, errors = 'ignore')
        tmm['_norm_title'] = tmm['Name'].map(normalize_title)
        tmm['_norm_artist'] = tmm['Artist'].map(normalize_artists_tmm)

        tmm_grouped = (
            tmm
            .groupby(['_norm_title', '_norm_artist'])
            .agg({
                'ISRC': list,
                'Apple - id': list
            })
            .reset_index()
        )

        merged = df_copy.merge(
            tmm_grouped,
            how = 'left',
            left_on = ['_norm_title', '_norm_artist'],
            right_on = ['_norm_title', '_norm_artist']
        )

        # Avoid ambiguous matches
        def is_valid_match(row):
            if isinstance(row['ISRC'], list):
                return len(row['ISRC']) == 1
            return False

        matched_mask = merged.apply(is_valid_match, axis=1)
        merged.rename(columns = {'Apple - id': 'Apple ID'}, inplace = True)

        matched_df = merged[matched_mask].copy()
        unmatched_df = merged[~matched_mask].copy()

        matched_df['ISRC'] = matched_df['ISRC'].apply(lambda x: x[0] if isinstance(x, list) else x)
        matched_df['Apple ID'] = matched_df['Apple ID'].apply(lambda x: x[0] if isinstance(x, list) else x)

        cols_to_drop = ['_norm_title', '_norm_artist']
        matched_df.drop(columns=cols_to_drop, inplace=True)
        unmatched_df.drop(columns=cols_to_drop, inplace=True)

        return matched_df, unmatched_df

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