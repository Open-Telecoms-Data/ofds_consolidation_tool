from typing import List, Tuple

import logging

from qgis.core import QgsVectorLayer, QgsProject, QgsFeature

from .network import Node, Span

logger = logging.getLogger(__name__)


def create_qgis_layer_from_nodes(
    nodes: List[Node],
) -> Tuple[QgsVectorLayer, List[Node]]:
    LAYER_NAME = "_ofds_consolidated_nodes"

    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    if len(project.mapLayersByName(LAYER_NAME)) > 0:
        project.removeMapLayers(
            [layer.id() for layer in project.mapLayersByName(LAYER_NAME)]
        )

    # Create the new QgsVectorLayer from consolidated Nodes
    # TODO: Tidy up (i.e. remove) this layer after we're done?
    layer_uri = "Point?crs=epsg:4326&index=yes"
    layer = QgsVectorLayer(layer_uri, LAYER_NAME, "memory")
    layer.setCustomProperty("skipMemoryLayersCheck", 1)

    layer_data = layer.dataProvider()
    assert layer_data  # type: ignore

    fields = Node.get_qgs_fields()

    layer.startEditing()
    layer_data.addAttributes(fields.toList())
    layer.commitChanges()

    logger.debug(f"Adding {len(nodes)} Nodes to QgsVectorLayer")

    new_nodes: List[Node] = list()

    # Create a new QgsFeature for each new Node, copying old Geometry
    #  + consolidated properties
    #  + new Nodes because featureId changes w/ a new layer
    for node in nodes:
        new_feature = QgsFeature(fields)
        new_feature.setGeometry(node.featureGeometry)
        for field in fields:
            if field.name() in node.properties:
                new_feature.setAttribute(field.name(), node.properties[field.name()])
        layer_data.addFeature(new_feature)
        new_nodes.append(
            Node(node.id, node.properties, new_feature.id(), new_feature.geometry())
        )

    layer.updateExtents()

    # TODO: Change visibility from True to False when we're not testing anymore
    #       or make it a setting?
    project.addMapLayer(layer, True)

    return (layer, new_nodes)


def create_qgis_layer_from_spans(
    spans: List[Span],
) -> Tuple[QgsVectorLayer, List[Span]]:
    LAYER_NAME = "_ofds_consolidated_spans"

    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    if len(project.mapLayersByName(LAYER_NAME)) > 0:
        project.removeMapLayers(
            [layer.id() for layer in project.mapLayersByName(LAYER_NAME)]
        )

    # Create the new QgsVectorLayer from consolidated Spans
    layer_uri = "LineString?crs=epsg:4326&index=yes"
    layer = QgsVectorLayer(layer_uri, LAYER_NAME, "memory")
    layer.setCustomProperty("skipMemoryLayersCheck", 1)

    layer_data = layer.dataProvider()
    assert layer_data  # type: ignore

    fields = Span.get_qgs_fields()

    layer.startEditing()
    layer_data.addAttributes(fields.toList())
    layer.commitChanges()

    logger.debug(f"Adding {len(spans)} Spans to QgsVectorLayer")

    new_spans: List[Span] = list()

    # Create a new QgsFeature for each new Node, copying old Geometry +
    # consolidated properties + new Nodes because featureId changes w/ a new layer
    for span in spans:
        new_feature = QgsFeature(fields)
        new_feature.setGeometry(span.featureGeometry)
        for field in fields:
            if field.name() in span.properties:
                new_feature.setAttribute(field.name(), span.properties[field.name()])
        layer_data.addFeature(new_feature)
        new_spans.append(
            Span(span.id, span.properties, new_feature.id(), new_feature.geometry())
        )

    layer.updateExtents()

    # TODO: Change visibility from True to False when we're not testing anymore
    #       or make it a setting?
    project.addMapLayer(layer, True)

    return (layer, new_spans)
