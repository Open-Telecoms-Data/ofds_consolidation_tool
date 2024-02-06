# OFDS Deduplication Tool

A tool to consolidate multiple data sets formatted using the Open Fibre Data Standard. Implemented as a QGIS plugin.


## Development Environment

## Setup

### Developing the QGIS Plugin

Handy links to look at:
* https://www.qgistutorials.com/en/docs/3/building_a_python_plugin.html
* https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/index.html#developing-python-plugins

Tools you'll need:
 * QGIS 3.28+
 * Qt5 Designer
 * `pyuic5` tool

You'll need to symlink your project directory into QGIS's local plugins directory, making the directory if it doesn't already exist, i.e.:

```bash
QGIS_PLUGINS_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
mkdir -p "$QGIS_PLUGINS_DIR"
ln -s ofds-dedup-tool/  "$QGIS_PLUGINS_DIR/ofds-dedup/"
```

There are a couple of useful helper plugins for developing your plugin, `Plugin Reloader` and `First Aid`, see: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#useful-plugins-for-writing-python-plugins

Be sure to configure your IDE/Python environment with access to QGIS python libraries, e.g.:
```bash
export PYTHONPATH="$PYTHONPATH:/usr/share/qgis/python/plugins:/usr/share/qgis/python"
```

See: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#a-note-on-configuring-your-ide-on-linux-and-windows