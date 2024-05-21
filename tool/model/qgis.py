from typing import IO, Any, List, Sequence, TextIO, Tuple, Dict

import json
import logging
import tempfile

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsFeature,
)

from .network import Feature, Node, Span

logger = logging.getLogger(__name__)


NODES_LAYER_NAME = "_ofds_consolidated_nodes"
SPANS_LAYER_NAME = "_ofds_consolidated_spans"


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

    json.dump(obj=geojson_obj, fp=fh)


def create_qgis_geojson_layer_from_nodes(
    nodes: List[Node],
) -> Tuple[QgsVectorLayer, List[Node]]:

    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    _delete_layers_with_name(project, SPANS_LAYER_NAME)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_ofds_nodes.geojson", delete=False
    ) as f:
        geojson_path = f.name
        write_geojson_from_features(f, nodes)

    layer = QgsVectorLayer(geojson_path, NODES_LAYER_NAME, "ogr")

    # Create new nodes referencing the new layer's featureIds & featureGeometry
    new_nodes = list(Node.from_qgis_feature(f) for f in list(layer.getFeatures()))

    project.addMapLayer(layer, True)

    return (layer, new_nodes)


def create_qgis_geojson_layer_from_spans(
    spans: List[Span],
) -> Tuple[QgsVectorLayer, List[Span]]:

    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    _delete_layers_with_name(project, SPANS_LAYER_NAME)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_ofds_spans.geojson", delete=False
    ) as f:
        geojson_path = f.name
        write_geojson_from_features(f, spans)

    layer = QgsVectorLayer(geojson_path, SPANS_LAYER_NAME, "ogr")

    # Create new nodes referencing the new layer's featureIds & featureGeometry
    new_spans = list(Span.from_qgis_feature(f) for f in list(layer.getFeatures()))

    project.addMapLayer(layer, True)

    return (layer, new_spans)
