from .library import Library
import os
from typing import Any
import yaml

class Utils:
    '''
    The class for utilities.
    '''

    @classmethod
    def read_yaml(cls,
                  path: str | bytes | os.PathLike[str]) -> Any:
        '''
        Read the YAML file.
        '''

        with open(path, 'r', encoding = 'utf-8') as f:
            yaml_file = yaml.safe_load(f)

        return yaml_file