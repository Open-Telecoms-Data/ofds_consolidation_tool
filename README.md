# OFDS Deduplication Tool

A tool to consolidate multiple data sets formatted using the Open Fibre Data Standard. Implemented as a QGIS plugin.

## Development Environment

## Developing the QGIS Plugin

Handy links to look at:

- https://www.qgistutorials.com/en/docs/3/building_a_python_plugin.html
- https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/index.html#developing-python-plugins

### Setup

Tools you'll need:

- QGIS 3.28+
- Qt5 Dev Tools, which should include:
  - Qt5 Designer
  - `pyuic5` tool

Install QGIS dev package:

```bash
sudo apt install qgis-dev # Ubuntu
sudo dnf install qgis-devel # Fedora
```

You'll need to symlink your project directory into QGIS's local plugins directory, making the directory if it doesn't already exist, i.e.:

From within the project git repo/directory:

```bash
cd path/to/ofds-consolidation-tool/

QGIS_PLUGINS_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
mkdir -p "$QGIS_PLUGINS_DIR"
ln -s "$PWD"  "$QGIS_PLUGINS_DIR"
```

There are a couple of useful helper plugins for developing your plugin, `Plugin Reloader` and `First Aid`, see: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#useful-plugins-for-writing-python-plugins

Be sure to configure your IDE/Python environment with access to QGIS python libraries, e.g.:

```bash
export PYTHONPATH="$PYTHONPATH:/usr/share/qgis/python/plugins:/usr/share/qgis/python"
```

See: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#a-note-on-configuring-your-ide-on-linux-and-windows

### Installing the plugin

In QGIS, go to `Plugins > Manage and Install Plugins`. Search for 'odfs', and activate our plugin in the list. A button should appear on the menu that says "Consolidate OFDS".

When you make changes to the plugin code, you can reload the plugin using `Plugins > Plugin Reloader` (the first time, configure it to reload the ofds_consolidation_tool plugin. After that you can use ctrl+F5).

### UI changes

You can open the `gui.ui` file in Qt5 Designer to make changes to the UI. After each change, run:

```
pyuic5 gui.ui > gui.py
```