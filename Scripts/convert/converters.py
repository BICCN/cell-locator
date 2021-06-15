import importlib.util
from pathlib import Path
from typing import Dict, Tuple, Generator

import model

__all__ = [
    'version_order', 'latest_version', 'infer_normalize', 'match', 'find_latest'
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


def infer_normalize(data: dict) -> Tuple[str, model.Document]:
    """Find the most-recent converter that can normalize the document.

    :returns: (version, document) — The inferred version and the normalized document.
    """

    for version in match():
        try:
            converter = converters[version]
            doc = converter.normalize(data)
            return version, doc
        except (KeyError, IndexError, AttributeError):
            continue
    raise ValueError('No converter can normalize the data')


def match(target: str = '') -> Generator[str, None, None]:
    """Find the most-recent versions matching the target.

    If target begins with 'd', then interpret the target as a date

    If target begins with a 'v', or has no prefix, interpret the target as a version
    directly.

    Substring matching is used for all cases; if the version or date begins with the
    target, then that version is matched. The most-recent matching version is chosen
    as defined in version_order.

    Since all versions would match the empty string, the most-recent available
    version is returned if target is empty or would otherwise match all versions.

    :returns: List of matching versions, in order of precedence (most-recent first)
    """

    key = target.lstrip('vd')

    if target.startswith('d'):
        key = f'+{key}'
    else:
        key = f'v{key}'

    for version in version_order:
        if key in version:
            yield version


def find_latest(target: str = '') -> Tuple[str, model.Converter]:
    """ Find the most-recent version and converter matching the target.

    See match() for details on matching logic.

    :returns: (version, converter) — The inferred version and the corresponding
    converter.
    """

    for version in match(target):
        return version, converters[version]

    raise ValueError(f'no version matches {target!r}')
