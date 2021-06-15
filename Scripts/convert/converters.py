import importlib.util
from pathlib import Path
from typing import Dict, Tuple, Generator

import model

__all__ = [
    'version_order', 'latest_version',
]

version_root = Path(__file__).parent.joinpath('versions')

# most-recent versions first
version_order = [
    'v0.1.0+2020.09.18',
    'v0.0.0+2020.08.26',
    'v0.0.0+2020.04.16',
    'v0.0.0+2019.01.26',
]
latest_version = version_order[0]


def load_converter(version: str) -> model.Converter:
    path = version_root.joinpath(version + '.py')
    spec = importlib.util.spec_from_file_location(
        'versions', str(path),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    converter = module.Converter
    return converter


converters: Dict[str, model.Converter] = {
    version: load_converter(version)
    for version in version_order
}
