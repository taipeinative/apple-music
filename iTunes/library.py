from collections import defaultdict
import msgpack
import os
import pandas as pd
import plistlib
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
    def data(self: 'Library') -> pd.DataFrame:
        '''
        The iTunes library data.
        '''
        return self.__df__.copy()

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

    def artist_chart(self: 'Library') -> pd.DataFrame:
        '''
        Retrieve the chart of artists, where the score is weighted by play counts and duration.
        '''

        artists = [artist for artistPair in self.__df__['Artists'].to_list() for artist in artistPair]
        artist_sorted = sorted(artists)
        chart_df = pd.Series(artist_sorted, name='Artists').value_counts().reset_index()

        chart_df.columns = pd.Index(['Artist', 'Occurance'])
        artist_score = {}

        for _, row in self.__df__.iterrows():
            artists = row['Artists']
            play_count = row['Play Count']
            total_time = row['Total Time']

            if not artists or pd.isna(play_count) or pd.isna(total_time):
                continue

            # Weighted score = Σ_i^n (ArtistOccurance_i (=1 if present, =0 if not present) *  PlayCount_i * TotalTime_i / NumberOfArtists_i)
            #                  where i is the index of the song in the dataframe, n is the number of songs.

            num_artists = len(artists)
            score = play_count * total_time.total_seconds() / num_artists
            for artist in artists:
                artist_score[artist] = artist_score.get(artist, 0) + score

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