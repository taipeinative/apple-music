from __future__ import annotations

import csv
import os
import pandas as pd

class PlaylistAccessor():
    '''
    Access the exported iTunes playlist file.
    '''

    def __init__(self: PlaylistAccessor,
                 path: str | bytes | os.PathLike) -> None:
        '''
        Initiate an accessor.
        '''

        self._buffer = []

        if isinstance(path, (str, bytes, os.PathLike)):
            if os.path.isfile(path):
                self._buffer = list(csv.reader(open(path, 'r', encoding='utf-16'), delimiter='\t'))
            else:
                raise FileNotFoundError(f'The file doesn\'t exist in the path: {path}')
        else:
            raise TypeError('The path should be a `str`, `bytes`, or `os.PathLike` object.')
        
    __name__ = 'PlaylistAccessor'
        
    def to_dataframe(self: PlaylistAccessor) -> pd.DataFrame:
        '''
        Convert the buffer into a pandas DataFrame.
        '''
        if not self._buffer:
            raise ValueError('No data in buffer to export.')
        
        header = [h.strip() for h in self._buffer[0]]
        data = [[cell.strip() for cell in row] for row in self._buffer[1:]]

        # Find the maximum row width
        max_width = max(len(row) for row in data)

        # Expand header if needed
        while len(header) < max_width:
            header.append(f'Extra_{len(header) + 1}')

        # Pad shorter rows (optional for safety)
        padded_data = [row + [''] * (len(header) - len(row)) for row in data]

        return pd.DataFrame(padded_data, columns=header)