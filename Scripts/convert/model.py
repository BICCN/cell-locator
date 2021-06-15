import abc
import dataclasses
from dataclasses import dataclass

from typing import List, Tuple

Vector3f = Tuple[float, float, float]
Matrix4f = Tuple[float, float, float, float,
                 float, float, float, float,
                 float, float, float, float,
                 float, float, float, float]


@dataclass
class Annotation:
    name: str = ''

    markup_type: str = 'ClosedCurve'
    representation_type: str = 'spline'
    thickness: float = 50

    # coordinate system should always be LPS in these dataclasses
    coordinate_system: str = 'LPS'
    coordinate_units: str = 'um'

    orientation: Matrix4f = (
        1.0, 0.0, 0.0, 0.25,
        0.0, 0.0, 1.0, -17.5,
        0.0, 1.0, 0.0, 22.25,
        0.0, 0.0, 0.0, 1.0,
    )

    points: List[Vector3f] = dataclasses.field(default_factory=list)


@dataclass
class Document:
    annotations: List[Annotation] = dataclasses.field(default_factory=list)
    current_id: int = 0
    reference_view: str = 'Coronal'
    ontology: str = 'Structure'
    stepSize: float = 0.5
    camera_position: Vector3f = (51.6226, -631.3969, -605.9925)
    camera_view_up: Vector3f = (-.5686, -.6042, .5582)


class Converter(abc.ABC):
    """ Utility to aid in conversion of Cell Locator files.

    "Specialized" -- a dict representation of a version-specific
    JSON. That representation may only work in one version of Cell Locator.

    "Normalized" -- a dataclass representation common to all versions of
    cell locator. An intermediate representation during the conversion process.
    """

    @classmethod
    @abc.abstractmethod
    def normalize(cls, data: dict):
        """Convert a specialized dict to a normalized Document"""
        pass

    @classmethod
    @abc.abstractmethod
    def specialize(cls, doc: Document):
        """Convert a normalized Document to a specialized dict."""
        pass
