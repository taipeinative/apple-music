from .utils import Utils
from collections import abc, defaultdict
from datetime import timedelta
import msgpack
import os
import pandas as pd
import plistlib
from rapidfuzz import fuzz
import re
from typing import Any, Iterable

class Library:
    '''
    The iTunes library.
    '''

    def __init__(self: 'Library', df: pd.DataFrame) -> None:
        self.__df__ = df

    def __repr__(self: 'Library') -> str:
        if self.is_valid():
            return f'iTunes Library <{len(self.__df__)} tracks>'
        else:
            return f'iTunes Library <invalid>'
    
    __name__ = 'Library'

    @property
    def artists(self: 'Library') -> pd.Series[str]:
        '''
        The series of track artists.
        '''
        artists: pd.Series = self.__df__['Artist']

        if Utils.get_type(artists) == '<class \'list\'>':
            artists = pd.Series(artists.explode().unique(), name = 'Artist').astype(str)

        else:
            artists = pd.Series(artists.unique(), name = 'Artist').astype(str)

        return Utils.custom_sort_values(artists)

    @property
    def data(self: 'Library') -> pd.DataFrame:
        '''
        The iTunes library data.
        '''
        return self.__df__.copy()

    @classmethod
    def from_excel(cls, path: str | bytes | os.PathLike[str], sheet: str | int) -> 'Library':
        '''
        Read a library from a Microsoft Excel file.
        '''

        def to_tuple(row: pd.Series) -> tuple:
            return row['Sub Tag 1'], row['Sub Tag 2'], row['Sub Tag 3']
        
        legacy_columns = ['Top Level', 'Second Level', 'Third Level']
        column_sets = ['Track ID', 'Name', 'Artist', 'Composer', 'Album', 'Genre', 'Year', 'Date Modified', 'Date Added', 'Play Count', 'Size', 'Total Time', 'Disc Number', 'Track Number', 'Vocal', 'Language', 'Sub Genres', 'Sub Tags']
        data = pd.read_excel(path, sheet_name = sheet, header = 0)

        if len(set(legacy_columns) & set(data.columns)) > 0:
            template = pd.DataFrame(columns = column_sets).astype({
                'Track ID': 'int64',
                'Year': 'int64',
                'Date Modified': 'datetime64[ns]',
                'Date Added': 'datetime64[ns]',
                'Play Count': 'int64',
                'Size': 'int64',
                'Total Time': 'timedelta64[ns]',
                'Disc Number': 'int64',
                'Track Number': 'int64'
            })

            data.rename(columns = {'Artists': 'Artist'}, errors = 'ignore', inplace = True)
            data.drop(columns = ['Rating'], errors = 'ignore', inplace = True)
            data = pd.concat([template, data], ignore_index = True)

            data['Vocal'] = data.get('Top Level', data['Vocal'])
            data['Language'] = data.get('Second Level', data['Language'])
            data['Sub Genres'] = data.get('Third Level', data['Sub Genres'])
            
        data['Sub Tags'] = data.apply(to_tuple, axis = 1)
        return Library(data[column_sets].copy())

    @classmethod
    def from_msgpack(cls, path: str | bytes | os.PathLike[str]) -> 'Library':
        '''
        Read a library from a message pack file.
        '''

        def denormalize(obj: Any) -> Any:
            if isinstance(obj, dict) and '__set__' in obj:
                return set(obj['__set__'])
            else:
                return obj

        def traverse(obj: Any) -> Any:
            if isinstance(obj, dict):
                if any(isinstance(v, str) for v in obj.values()):
                    pass

                denormalized_obj = denormalize(obj)
                
                if isinstance(denormalized_obj, set):
                    return {traverse(v) for v in denormalized_obj}

                return {k: traverse(v) for k, v in obj.items()}
            
            elif isinstance(obj, list):
                return [traverse(v) for v in obj]
            
            else:
                return denormalize(obj)
            
        with open(path, 'rb') as f:
            data = msgpack.unpackb(f.read(), raw = False)

        denormalized = [traverse(row) for row in data]
        df = pd.DataFrame(denormalized)

        type_dict = {
            'Track ID': 'int64',
            'Year': 'int64',
            'Date Modified': 'datetime64',
            'Date Added': 'datetime64',
            'Play Count': 'int64',
            'Size': 'int64',
            'Total Time': 'timedelta64'
        }

        for col in df.columns:
            match type_dict.get(col):
                case 'int64':
                    df[col] = pd.to_numeric(df[col])
                
                case 'datetime64':
                    df[col] = pd.to_datetime(df[col])

                case 'timedelta64':
                    df[col] = pd.to_timedelta(df[col])

                case _:
                    pass
        
        return Library(df)
    
    @classmethod
    def from_xml(cls, path: str | bytes | os.PathLike[str]) -> 'Library':
        '''
        Read a library from a XML file.
        '''

        if isinstance(path, (str, bytes, os.PathLike)) and os.path.isfile(path):
            with open(path, 'rb') as fp:
                library = plistlib.load(fp)

            tracks = library['Tracks']
            track_list = []
            for track_id, track_info in tracks.items():
                track_list.append(track_info)
            df = pd.DataFrame(track_list).loc[:, ['Track ID', 'Name', 'Artist', 'Composer', 'Album', 'Genre', 'Year', 'Date Modified', 'Date Added', 'Play Count', 'Size', 'Total Time', 'Disc Number', 'Track Number']]
            df['Play Count'] = df['Play Count'].fillna(0).astype(int)
            df['Total Time'] = pd.to_timedelta(df['Total Time'], unit='ms')
            df['Disc Number'] = df['Disc Number'].apply(lambda x: str(int(x)) if pd.notnull(x) else None)
            df['Track Number'] = df['Track Number'].apply(lambda x: str(int(x)) if pd.notnull(x) else None)

            playlist_dict = {}
            for playlist in library['Playlists']:
                playlist_list = playlist.get('Playlist Items', list())
                if len(playlist_list) > 0:
                    track_set = set()
                    for track in playlist_list:
                        track_set.add(track['Track ID'])
                    playlist_dict[playlist['Name']] = track_set

            track_to_playlists = defaultdict(set)
            for playlist_name, track_ids in playlist_dict.items():
                for track_id in track_ids:
                    track_to_playlists[track_id].add(playlist_name)
            df['Tags'] = df['Track ID'].map(lambda tid: track_to_playlists.get(tid, set()))
            return Library(df)
        
        else:
            raise ValueError('Invalid path.')

    @classmethod
    def merge(cls, prev: 'Library', next: 'Library',
              artist_map: dict[str, str | list[str]] = {},
              artists_with_comma: list[str] = [],
              name_map: dict[str, dict[str, str] | list[dict[str, str | list[str]]]] = {}) -> LibraryMerger:
        '''
        Try to merge two iTunes libraries.
        '''

        def create_key_column(df: pd.DataFrame, source: str, key: str) -> pd.DataFrame:
            df = df.copy()
            df[key] = df[source].apply(
                lambda x: ','.join(sorted(x)) if isinstance(x, list) else str(x)
            )
            return df

        def drop_key_column(key: str, dfs: list[pd.DataFrame]) -> None:
            for df in dfs:
                df.drop(columns = [key], errors = 'ignore', inplace = True)

        def get_rename_map(cols: list[str]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
            n_series = {}
            p_series = {}
            x_series = {}
            for col in cols:
                n_series[f'{col}_n'] = col
                p_series[f'{col}_p'] = col
                x_series[f'{col}_x'] = col
            return n_series, p_series, x_series

        def handle_artists(lib: 'Library') -> pd.DataFrame:
            def flatten_replace(arr: list[str]) -> list[str]:
                result = []
                for x in arr:
                    val = artist_map.get(x, x)
                    if isinstance(val, list):
                        result.extend(val)
                    else:
                        result.append(val)
                return result
            
            artists = lib.__df__['Artist']
            artists_type = Utils.get_type(artists)
            if artists_type == '<class \'list\'>':
                lib.__df__['Artist'] = artists.apply(flatten_replace)
            if artists_type == '<class \'str\'>':
                lib = lib.nested_artists(artist_map, artists_with_comma)

            return lib.__df__
        
        def handle_names(df: pd.DataFrame) -> pd.DataFrame:
            def is_equal(source: str | list, target: str | list) -> bool:
                return set(to_list(source)) == set(to_list(target))
            
            def row_replace(row: pd.Series) -> str:
                replacers = name_map.get('complex', [])
                assert isinstance(replacers, list)
                for r in replacers:
                    r_artist = r.get('artist', [])
                    r_alias = to_list(r.get('alias', []))
                    if is_equal(row['Artist'], r_artist):
                        if row['Name'] in r_alias:
                            return str(r.get('title', row['Name']))
                return row['Name']

            def to_list(x: Any) -> list:
                if isinstance(x, str):
                    return [x]
                if isinstance(x, abc.Iterable):
                    return list(x)
                return []
            
            df = df.copy()
            df['Name'] = df.apply(row_replace, axis = 1)
            return df

        if not(next.is_valid() and prev.is_valid()):
            raise ValueError('At least one of the libraries is corrupted.')

        next_df: pd.DataFrame = create_key_column(handle_artists(next.copy()), 'Artist', 'ArtistKey')
        prev_df: pd.DataFrame = create_key_column(handle_artists(prev.copy()), 'Artist', 'ArtistKey')

        if name_map.get('complex'):
            next_df = handle_names(next_df)
            prev_df = handle_names(prev_df)
        
        if name_map.get('simple'):
            replacer = name_map['simple']
            assert isinstance(replacer, dict)
            next_df['Name'].replace(replacer, inplace = True)
            prev_df['Name'].replace(replacer, inplace = True)

        indices = ['Name', 'ArtistKey']
        col_from_new = ['Composer', 'Date Added', 'Date Modified', 'Disc Number', 'Play Count', 'Size', 'Tags', 'Total Time', 'Track ID', 'Track Number']
        combined_indices = indices.copy()
        combined_indices.extend(col_from_new)
        n_renamer, p_renamer, x_renamer = get_rename_map(col_from_new)

        merged = prev_df.merge(
            next_df[combined_indices],
            on = indices,
            how = 'outer',
            indicator = True,
            suffixes = ('_p', '_n')
        )

        matched = merged.loc[merged['_merge'] == 'both'].copy().rename(columns = n_renamer)
        matched = matched[prev_df.columns]
        matched = matched.drop(columns = [f'{col}_p' for col in col_from_new], errors = 'ignore')
        matched = matched.merge(
            next_df[combined_indices],
            on = indices,
            how = 'left'
        )

        matched = matched.drop(columns = [f'{col}_y' for col in col_from_new], errors = 'ignore').rename(columns = x_renamer)
        matched = matched[~matched.duplicated(indices)]
        next_only = merged.loc[merged['_merge'] == 'right_only', indices].merge(
            next_df, on = indices, how = 'left'
        )

        prev_only = merged.loc[merged['_merge'] == 'left_only'].copy().rename(columns = p_renamer)[prev_df.columns]
        drop_key_column('ArtistKey', [matched, next_only, prev_only])
        return LibraryMerger(matched, next_only, prev_only)

    def artist_chart(self: 'Library') -> pd.DataFrame:
        '''
        Retrieve the chart of artists, where the score is weighted by play counts and duration.
        '''

        chart_df = self.__df__['Artist'].explode().value_counts().reset_index()
        chart_df.columns = pd.Index(['Artist', 'Occurance'])
        artist_score: dict[str, float] = {}

        for _, row in self.__df__.iterrows():
            artists: list[str] | str = row['Artist']
            play_count: int = row['Play Count']
            total_time: timedelta = row['Total Time']

            if not artists or pd.isna(play_count) or pd.isna(total_time):
                continue

            # Weighted score = Σ_i^n (ArtistOccurance_i (=1 if present, =0 if not present) *  PlayCount_i * TotalTime_i / NumberOfArtists_i)
            #                  where i is the index of the song in the dataframe, n is the number of songs.

            if isinstance(artists, list):
                num_artists = len(artists)
                score = play_count * total_time.total_seconds() / num_artists
                for artist in artists:
                    artist_score[artist] = artist_score.get(artist, 0) + score
            
            else:
                score = play_count * total_time.total_seconds()
                artist_score[artists] = artist_score.get(artists, 0) + score

        weighted_df = pd.DataFrame([
            {'Artist': artist, 'Score': round(score, 2)} for artist, score in artist_score.items()
        ])

        chart_df = weighted_df.join(chart_df.set_index('Artist'), on='Artist').sort_values(['Score', 'Occurance'], ascending=False).reset_index(drop=True)
        return chart_df

    def copy(self: 'Library') -> 'Library':
        '''
        Deep copy the library object.
        '''
        return Library(self.__df__.copy(deep = True))

    def filter(self: 'Library', column: str, whitelist: Iterable | None = None, blacklist: Iterable | None = None) -> 'Library':
        '''
        Filter values according to the whitelist and the blacklist. The priority of blacklist is higher than that of whitelist.
        '''

        if self.is_valid():
            new_lib = self.copy()

            if column == 'Tags':
                blackset = set() if blacklist is None else set(blacklist)
                whiteset = set() if whitelist is None else set(whitelist)
                new_lib.__df__ = new_lib.__df__[new_lib.__df__[column].apply(lambda tags: not bool(tags & blackset))]
                if len(whiteset) > 0:
                    new_lib.__df__ = new_lib.__df__[new_lib.__df__[column].apply(lambda tags: bool(tags & whiteset))]
                    new_lib.__df__[column] = new_lib.__df__[column].apply(lambda tags: tags & whiteset)
                
                new_lib.__df__ = new_lib.__df__.reset_index(drop = True)
                return new_lib

            elif column in self.__df__.columns:
                new_lib.__df__ = new_lib.__df__[~new_lib.__df__.isin([] if blacklist is None else blacklist)]
                if isinstance(whitelist, list) and len(whitelist) > 0:
                    new_lib.__df__ = new_lib.__df__[new_lib.__df__.isin(whitelist)]
                
                new_lib.__df__ = new_lib.__df__.reset_index(drop = True)
                return new_lib

            else:
                raise ValueError('The specified column doesn\'t exist.')

        else:
            raise ValueError('The library is corrupted.')

    def is_valid(self: 'Library') -> bool:
        '''
        Verify the library integrity.
        '''

        if self.__df__ is None:
            return False
        if not isinstance(self.__df__, pd.DataFrame):
            return False
        
        obligated_cols = ['Track ID', 'Name', 'Artist', 'Composer', 'Album', 'Genre', 'Year', 'Date Modified', 'Date Added', 'Play Count', 'Size', 'Total Time', 'Disc Number', 'Track Number']
        
        if sum([(col in obligated_cols) for col in self.__df__.columns.to_list()]) != len(obligated_cols):
            return False
        else:
            return True

    def map(self: 'Library', column: str, table: dict) -> 'Library':
        '''
        Map values of the library column based on the table.
        '''

        if self.is_valid():
            new_lib = self.copy()

            if column == 'Tags':
                new_lib.__df__[column] = new_lib.__df__[column].apply(lambda tag_set: {table.get(tag, tag) for tag in tag_set})
                return new_lib

            elif column in self.__df__.columns:
                new_lib.__df__[column] = new_lib.__df__[column].map(table)
                return new_lib

            else:
                raise ValueError('The specified column doesn\'t exist.')

        else:
            raise ValueError('The library is corrupted.')

    def nested_artists(self: 'Library', table: dict[str, str | list[str]] = {}, artists_with_comma: list[str] = []) -> 'Library':
        if not self.is_valid():
            raise ValueError('The library is corrupted.')
        
        def extract_artists(row: pd.Series) -> list[str]:
            artist_field = row.get('Artist', '')
            title_field = row.get('Name', '')

            if isinstance(artist_field, str) and isinstance(title_field, str):
                main = split_artist(artist_field)
                feat = extract_feat_artist(title_field)
                mapped = []
                for artist in main + feat:
                    mapped_artist = table.get(artist, artist)
                    if isinstance(mapped_artist, list):
                        mapped.extend(mapped_artist)
                    else:
                        mapped.append(mapped_artist)
                seen = set()
                unique = []
                for artist in mapped:
                    if artist not in seen:
                        seen.add(artist)
                        unique.append(artist)
                
                return unique
            
            elif isinstance(artist_field, list):
                return artist_field
            
            else:
                raise ValueError('The artist field must be strings or list of strings.')

        def extract_feat_artist(title: str) -> list[str]:
            non_artist = {'vip mix', 'vip remix', 'house remix', 'dance remix', 'night beat remix', 'remix', 'mix'}
            matches = re.compile(r'[\[\(](.*?)[\]\)]').finditer(title)
            feats = []

            for match in matches:
                content = match.group(1)
                check = content.lower().strip()
                if 'feat' in check or 'with' in check:
                    cleaned = re.sub(r'^(feat\.?|with)\s+', '', content, flags=re.IGNORECASE)
                    parts = re.split(r',|&', cleaned)
                    feats.extend([p.strip() for p in parts if p.strip()])
                elif any(word in check for word in non_artist):
                    remix_match = re.match(r'(.*?)\s+(?:' + '|'.join(non_artist) + r')', content, flags=re.IGNORECASE)
                    if remix_match:
                        remix_artist = remix_match.group(1).strip()
                        if remix_artist:
                            feats.append(remix_artist)

            return feats or []

        def protect_comma(artist: str) -> str:
            for case in artists_with_comma:
                artist = artist.replace(case, case.replace(',', '<COMMA>'))
            return artist

        def split_artist(artist: str) -> list[str]:
            artist_str = protect_comma(artist).replace(' & ', ', ')
            return [name.strip().replace('<COMMA>', ',') for name in artist_str.split(',')]

        new_lib = self.copy()
        new_lib.__df__['Artist'] = new_lib.__df__.apply(extract_artists, axis = 1)
        return new_lib

    def search(self: 'Library', q: str, columns: str | list[str] | None = None, contains: bool = True) -> pd.DataFrame:
        '''
        Search in the iTunes library.
        '''
        if not self.is_valid():
            raise ValueError('The library is corrupted.')
        
        if isinstance(columns, str) and columns in self.__df__.columns:
            cols = [columns]

        elif isinstance(columns, list):
            cols = list(set(columns) & set(self.__df__.columns))
            if not cols:
                cols = self.__df__.select_dtypes(include=['object']).columns.tolist()
        
        else:
            cols = self.__df__.select_dtypes(include=['object']).columns.tolist()

        q_norm = Utils.normalize_value(q)
        score_df = pd.DataFrame(index = self.__df__.index)

        for col in cols:
            normalized_col = self.__df__[col].map(lambda x: Utils.normalize_value(x))

            if contains:
                score_df[col + '_score'] = normalized_col.map(lambda x: 100 if q_norm in x else 0)

            else:
                score_df[col + '_score'] = normalized_col.map(lambda x: fuzz.ratio(q_norm, Utils.normalize_value(x)))

        score_df['FinalScore'] = score_df.max(axis=1)
        
        if contains:
            score_df = score_df[score_df['FinalScore'] > 0]
        else:
            score_df = score_df[score_df['FinalScore'] >= 50]
        
        score_df = score_df.sort_values(by='FinalScore', ascending = False)
        return self.__df__.copy().loc[score_df.index].reset_index(drop = True)

    def to_csv(self: 'Library',
               path: str | bytes | os.PathLike[str]) -> None:
        '''
        Export the library to a CSV file.
        '''

        if self.is_valid():
            csv = self.__df__.copy(deep=True)
            csv['Total Time'] = csv['Total Time'].astype(str).apply(lambda x:x.split(' ')[2])
            csv.to_csv(path, index = False) # type: ignore

    def to_dataframe(self: 'Library') -> pd.DataFrame:
        '''
        Export the library to a Pandas DataFrmae.
        '''

        if self.is_valid():
            return self.__df__.copy()
        else:
            raise ValueError('The library is corrupted.')
        
    def to_msgpack(self: 'Library',
                   path: str | bytes | os.PathLike[str]) -> None:
        '''
        Export the library to a message pack file.
        '''
        
        def normalize(obj: Any) -> Any:
            if isinstance(obj, type(pd.NA)) or isinstance(obj, type(pd.NaT)):
                return None

            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()

            if isinstance(obj, pd.Timedelta):
                return str(obj)

            if isinstance(obj, set):
                return {'__set__': list(obj)}

            return obj
        
        def traverse(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: traverse(v) for k, v in obj.items()}
            
            elif isinstance(obj, list):
                return [traverse(v) for v in obj]
            
            else:
                return normalize(obj)
        
        if self.is_valid():
            records = self.__df__.to_dict(orient='records')
            normalized = [traverse(row) for row in records]
            with open(path, 'wb') as f:
                f.write(msgpack.packb(normalized, use_bin_type = True)) # type: ignore

        else:
            raise ValueError('The library is corrupted.')

class LibraryMerger:
    '''
    The container of the iTunes library merge result.
    '''
    
    def __init__(self: 'LibraryMerger', matched: pd.DataFrame, next_only: pd.DataFrame, prev_only: pd.DataFrame) -> None:
        self.__mdf__ = matched
        self.__ndf__ = next_only
        self.__pdf__ = prev_only

    def __repr__(self: 'LibraryMerger') -> str:
        return f'iTunes Library Merge Result <Matched/Left Only/Right Only: {len(self.__mdf__)}/{len(self.__ndf__)}/{len(self.__pdf__)}>'

    __name__ = 'LibraryMerger'

    @property
    def matched(self: 'LibraryMerger') -> pd.DataFrame:
        '''
        Matched tracks.
        '''
        return self.__mdf__.copy(deep = True)
    
    @matched.setter
    def matched(self: 'LibraryMerger', input: pd.DataFrame) -> None:
        self.__mdf__ = input

    @property
    def next_only(self: 'LibraryMerger') -> pd.DataFrame:
        '''
        The tracks that only appear on the next library.
        '''
        return self.__ndf__.copy(deep = True)
    
    @next_only.setter
    def next_only(self: 'LibraryMerger', input: pd.DataFrame) -> None:
        self.__ndf__ = input

    @property
    def prev_only(self: 'LibraryMerger') -> pd.DataFrame:
        '''
        The tracks that only appear on the previous library.
        '''
        return self.__pdf__.copy(deep = True)
    
    @prev_only.setter
    def prev_only(self: 'LibraryMerger', input: pd.DataFrame) -> None:
        self.__npf__ = input
    
    def as_lib(self: 'LibraryMerger', include_next: bool = True, include_prev: bool = False) -> 'Library':
        '''
        Retrieve the matched result as a library.
        '''

        data = self.__mdf__.copy()
        if include_next:
            data = pd.concat([data, self.__ndf__])

        if include_prev:
            data = pd.concat([data, self.__pdf__])

        data = data.sort_values('Track ID', ignore_index = True)
        return Library(data)