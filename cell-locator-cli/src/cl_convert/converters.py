import importlib.util
import sys
from pathlib import Path
from typing import Dict, Tuple, Generator

from cl_convert import model

__all__ = [
    'version_order', 'latest_version', 'infer_normalize', 'match', 'find_latest'
]

version_root = Path(__file__).parent.joinpath('versions')

# most-recent versions first
version_order = [
    'v0.2.1+2022.03.04',
    'v0.2.0+2021.08.12',
    'v0.1.1+2021.06.11',
    'v0.1.0+2020.09.18',
    'v0.0.0+2020.08.26',
    'v0.0.0+2020.04.16',
    'v0.0.0+2019.01.26',
]
latest_version = version_order[0]


def load_converter(version: str) -> model.Converter:
    path = version_root.joinpath(version + '.py')
    spec = importlib.util.spec_from_file_location(
        version, path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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

    Prefix with ``d`` to interpret as a date. Prefix with ``v``, or no prefix,
    to interpret as a literal version.

    ===================== ========= ========= ===========
    Example Versions      ``v1.1``  ``v1.1.`` ``d2020.``
    ===================== ========= ========= ===========
    ``1.1.0+2019.02.01``  yes       yes       no
    ``1.1.1+2020.02.07``  yes       yes       yes
    ``1.2.0+2020.05.01``  no        no        yes
    ``1.10.1+2021.03.01`` yes       no        no
    ===================== ========= ========= ===========

    :param target: String describing target versions.

    :returns: Matching versions, in order of precedence (most-recent first)
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
    """Find the most-recent matching version and converter.

    :param target: The target version string. See match() for details on matching logic.
    :return: The inferred version and the corresponding converter.
    """

    for version in match(target):
        return version, converters[version]

    raise ValueError(f'no version matches {target!r}')
