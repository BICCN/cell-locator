import abc
import dataclasses
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

__all__ = ['Annotation', 'Document', 'Converter', 'versioned']

Vector3f = Tuple[float, float, float]
Matrix4f = Tuple[float, float, float, float,
                 float, float, float, float,
                 float, float, float, float,
                 float, float, float, float]

@dataclass
class Structure:
    id: int
    acronym: str

@dataclass
class Point:
    position: Vector3f
    structure: Optional[Structure] = None

    def __iter__(self):
        # enables unpacking like `x, y, z = point`
        return iter(self.position)

@dataclass
class Annotation:
    """Store minimal information about a single annotation """

    name: str = ''

    markup_type: str = 'ClosedCurve'
    representation_type: str = 'spline'
    """Type for a closed curve annotation; ex 'spline' or 'polyline'."""
    thickness: float = 50
    """Thickness of the annotation model"""

    # coordinate system should always be LPS in these dataclasses
    coordinate_system: str = 'LPS'
    """Should always be LPS here; older versions of Slicer use RAS."""
    coordinate_units: str = 'um'
    """Should be um for CCF atlas, mm for MNI atlas."""

    orientation: Matrix4f = (
        1.0, 0.0, 0.0, 0.25,
        0.0, 0.0, 1.0, -17.5,
        0.0, 1.0, 0.0, 22.25,
        0.0, 0.0, 0.0, 1.0,
    )
    """A transformation matrix storing the orientation of the slicing plane."""

    points: List[Point] = dataclasses.field(default_factory=list)
    """Control point positions for the annotation markup."""


@dataclass
class Document:
    annotations: List[Annotation] = dataclasses.field(default_factory=list)

    current_id: int = 0
    """Index of the currently-selected annotation."""

    reference_view: str = 'Coronal'
    """Initial reference view. Ex. 'Coronal', 'Axial', or 'Sagittal'."""
    ontology: str = 'Structure'
    """Initial atlas ontology. Ex. 'Structure', 'Layer', or 'None'"""

    stepSize: float = 0.5
    """Distance in :py:attr:`Annotation.coordinate_units` to move slice plane in 
    Explore mode.
    """

    camera_position: Vector3f = (51.6226, -631.3969, -605.9925)
    """Initial camera position."""
    camera_view_up: Vector3f = (-.5686, -.6042, .5582)
    """Initial camera 'up' vector."""


def versioned(func):
    """Automatically infer version string from calling filename.

    When the caller's filename is formatted ``'v{version}.py'``, extract
    ``{version}`` from that filename and set the ``"version"`` key in the result.

    For example, in the file ``v1.0.0.py``::

        @versioned
        def specialize():
            return {}

        data = specialize()
        assert data['version'] == '1.0.0'
    """

    # get the calling frame's filename; extract the version
    frame = inspect.stack()[1]
    file = frame[0].f_code.co_filename
    version = Path(file).stem.lstrip('v')

    def wrap(*arg, **kwarg):
        data = func(*arg, **kwarg)
        data['version'] = version
        return data

    return wrap


class Converter(abc.ABC):
    """ Utility to aid in conversion of Cell Locator files.

    "Specialized" -- a dict representation of a version-specific
    JSON. That representation may only work in one version of Cell Locator.

    "Normalized" -- a dataclass representation common to all versions of
    cell locator. An intermediate representation during the conversion process.

    For example, the flow to update a file to a different version would be:

    >>> doc = old_converter.normalize(data)
    >>> new_data = new_converter.specialize(doc)

    It is also easier to perform manipulations on a ``Document``. For example:

    >>> doc = converter.normalize(data)
    >>> for annotation in doc.annotations:
    ...     annotation.name = annotation.name.lower()
    >>> data = converter.specialize(data)
    """

    @classmethod
    @abc.abstractmethod
    def normalize(cls, data: dict):
        """Convert a specialized dict to a normalized Document"""
        pass

    @classmethod
    @abc.abstractmethod
    def specialize(cls, doc: Document):
        """Convert a normalized Document to a specialized dict; specific to this
        version.
        """
        pass
