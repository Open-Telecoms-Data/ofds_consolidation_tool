import collections.abc
import logging

from qgis.core import (
    QgsMapLayer,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
)

logger = logging.getLogger(__name__)

# Display our data on the embedded maps in the Web Mercator CRS (aka EPSG 3857),
# as used by OpenStreetMap.
# https://epsg.io/3857
EPSG3857 = QgsCoordinateReferenceSystem("EPSG:3857")
# WGS84 as used by GeoJson https://epsg.io/4326
EPSG4328 = QgsCoordinateReferenceSystem("EPSG:4326")


def isQgsMapLayerOFDS(layer: QgsVectorLayer) -> bool:
    """
    Try to figure out if a given layer is OFDS or not, so we can warn users if they try to use a non-OFDS layer with the consolidation tool.
    """
    # It must be either a Points layer (Nodes) or a Lines layer (Spans)
    # TODO: It's features must have an "id" property
    # TODO: It's features must have a "network" properties, which is an object, which has an "id" property
    if (layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry) or (
            layer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry):
        return True


def getOpenStreetMapLayer(project: QgsProject) -> QgsMapLayer:
    """
    Get the OpenStreetMap layer, creating it if necessary.
    """
    # TODO: Tidy up OSM layer when we're done with it, i.e. remove it from the project and set this cache to none when the user closes the UI

    OSM_LAYER_NAME = "_ofds_consolidation_tool_OpenStreetMap"

    try:
        osm_layer = project.mapLayersByName(OSM_LAYER_NAME)[0]
    except IndexError:
        osm_layer = QgsRasterLayer(
            "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0&http-header:referer=",
            "OpenStreetMap",
            "wms",
        )

        if not osm_layer.isValid():
            logger.error("Failed to load OSM layer")
            raise Exception("Failed to load OpenStreetMap layer") from None

        project.addMapLayer(
            osm_layer, False
        )  # False to prevent adding it to the legend

        # OpenStreetMap is EPSG 3857
        osm_layer.setCrs(EPSG3857)

    return osm_layer


# Thanks to https://github.com/ScriptSmith/socialreaper/blob/master/socialreaper/tools.py#L8
def flatten(obj, parent_key=False, separator="."):
    """
    Turn a nested dictionary into a flattened dictionary
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in obj.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)
