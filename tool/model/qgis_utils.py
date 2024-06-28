from typing import IO, Any, List, Sequence, Tuple, Dict, Type, TypeVar

import json
import logging
import tempfile

from PyQt5.QtCore import QVariant

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
)

from .network import Feature, Node, Span

logger = logging.getLogger(__name__)


NODES_LAYER_NAME = "_ofds_consolidated_nodes"
SPANS_LAYER_NAME = "_ofds_consolidated_spans"


class QVariantJSONEncoder(json.JSONEncoder):
    """Extended JSON Decoder with support for QVariant"""

    def default(self, o: Any):
        if isinstance(o, QVariant):
            if o.isNull():
                return None
        return o


def _delete_layers_with_name(project: QgsProject, name: str):
    if len(project.mapLayersByName(name)) > 0:
        project.removeMapLayers([layer.id() for layer in project.mapLayersByName(name)])


def write_geojson_from_features(fh: IO[str], features: Sequence[Feature]):
    geojson_features = list()

    for feat in features:
        geojson_feat = {
            "type": "Feature",
            "properties": feat.properties.copy(),
            "geometry": json.loads(feat.featureGeometry.asJson()),
        }
        geojson_features.append(geojson_feat)

    geojson_obj: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": geojson_features,
    }

    json.dump(obj=geojson_obj, fp=fh, cls=QVariantJSONEncoder, indent=4)


FeatureT = TypeVar("FeatureT", bound=Feature)


def create_qgis_geojson_layer_from_features(
    features: Sequence[FeatureT], layer_name: str, cls: Type[FeatureT]
) -> Tuple[QgsVectorLayer, Sequence[FeatureT]]:
    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    _delete_layers_with_name(project, layer_name)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f"{layer_name}.geojson", delete=False
    ) as f:
        geojson_path = f.name
        write_geojson_from_features(f, features)

    layer = QgsVectorLayer("GeoJSON:" + geojson_path, layer_name, "ogr")

    # Create new nodes referencing the new layer's featureIds & featureGeometry
    new_features = list(cls.from_qgis_feature(f) for f in list(layer.getFeatures()))

    project.addMapLayer(layer, True)

    return layer, new_features


def create_qgis_geojson_layer_from_nodes(
    nodes: List[Node],
) -> Tuple[QgsVectorLayer, List[Node]]:
    layer, new_nodes = create_qgis_geojson_layer_from_features(
        features=nodes, layer_name=NODES_LAYER_NAME, cls=Node
    )
    return layer, list(new_nodes)


def create_qgis_geojson_layer_from_spans(
    spans: List[Span],
) -> Tuple[QgsVectorLayer, List[Span]]:
    layer, new_spans = create_qgis_geojson_layer_from_features(
        features=spans, layer_name=SPANS_LAYER_NAME, cls=Span
    )
    return layer, list(new_spans)
