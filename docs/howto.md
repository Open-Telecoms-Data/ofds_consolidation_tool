# How to use the OFDS consolidation tool

## Install QGIS and the plugin

The consolidation tool is a [QGIS](https://qgis.org/) plugin. First, follow the [installation instructions for QGIS]() for your operating system. The tool works with QGIS version 3.28 and higher. If you have an older version of QGIS installed, you need to upgrade it.

<!--
To install the plugin, you need an internet connection, but after that it will work offline.

1. Open QGIS. Go to Plugins > Manage and Install Plugins.
2. Search for "OFDS Consolidation Tool" and click "Install Plugin".
-->

The plugin is currently in development beta, and not yet available from the QGIS plugin libraries. To install the plugin for testing, follow the instructions in [Development > Enabling and running the plugin]().

## Your data

You should start with node and span data for the two networks you want to compare.

The network data need to be in [geoJSON]() format compatible with the [Open Fibre Data Standard]().

An example of this is; a node network:

```

```

and a span network:

```

```

## Consolidating networks

1. Add your two span and node data files as layers to the project by going to Layer > Add Layer > Add Vector Layer.
2. Navigate to your geojson files one at a time under 'Source' and press 'Add' for each one. They should appear under the Layers list, and appear visually on the map window.
3. Optionally, adjust the colours and thicknesses of each layer by double clicking on each layer in the Layers list.

Tip: To view a map underneath the nodes and spans, go to the Browser window > XYZ tiles and double click Open Street Map or other map tiles of your choice. In the Layers list, make sure the nodes and spans are above the map layer to see them. (TODO: is this the default? How to add maps if there are none?) Adding the map is not necessary for using the tool, but it may make it easier to understand your data.

4. Click "Consolidate OFDS" in the toolbar.

 