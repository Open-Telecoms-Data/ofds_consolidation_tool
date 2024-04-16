# Development

If you want to make changes to the consolidation tool code, follow these instructions to connect a local copy of the plugin with your QGIS installation.

QGIS plugins are written in pure Python, and external libraries must be bundled with the tool, so we try to keep these dependencies to a minimum.

To read more about how to develop plugins for QGIS in general, see:

- https://www.qgistutorials.com/en/docs/3/building_a_python_plugin.html
- https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/index.html#developing-python-plugins

## Setup

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

### Enabling and running the plugin in QGIS

Symlink your project directory into QGIS's local plugins directory, making the directory if it doesn't already exist.

From within the project git repo/directory (NOTE: the project folder *must* only use underscores and letters, no hyphens):

```bash
cd path/to/ofds_consolidation_tool/

QGIS_PLUGINS_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
mkdir -p "$QGIS_PLUGINS_DIR"
ln -s "$PWD"  "$QGIS_PLUGINS_DIR"
```

Configure your IDE/Python environment with access to QGIS python libraries:

```bash
export PYTHONPATH="$PYTHONPATH:/usr/share/qgis/python/plugins:/usr/share/qgis/python"
```

See: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#a-note-on-configuring-your-ide-on-linux-and-windows

In QGIS, go to `Plugins > Manage and Install Plugins`. Search for 'odfs', and activate our plugin in the list. A button should appear on the menu that says "Consolidate OFDS".

Install the `Plugin Reloader` plugin so you can reload any code changes you make without having to restart QGIS. #todo

You may also find it helpful to install the `First Aid` plugin; see: https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#useful-plugins-for-writing-python-plugins

When you make changes to the plugin code, you can reload the plugin using `Plugins > Plugin Reloader`. The first time, configure it to reload the ofds_consolidation_tool plugin. After that you can use ctrl/cmd+F5.

### UI changes

Open the `gui.ui` file in Qt5 Designer to make changes to the UI. After each change, run:

```
pyuic5 gui.ui > gui.py
```

## Contribution guidelines

The OFDS Consolidation Tool is open source, and we welcome issues and merge requests from members of the community who wish to fix bugs or make other improvements.

We are a small development team, splitting our time between this and other projects, so there may be a delay on testing and merging any new code, particularly any large new features. We will do our best to respond to small fixes in a timely manner, and please let us know if you are actively 

### Commit Messages

To enable automatic Semantic Versioning, please use [Angular-like commit convention](https://www.conventionalcommits.org/en/v1.0.0/#summary).

To get started quickly, follow a structure like:

```
<type>(<scope>): Short description

Long description
```

Where `<type>` is one of `feat` (minor version bump), `fix`
(patch version bump) or `chore` (no version change, e.g. documentation changes).

The `<scope>` is per-project, and up to us to decide what to use, e.g. `tool` for tool changes, `docs` for documentation changes, `gui` for pure GUI changes. Use more as needed/relevent. For example:

```
feat(tool): A new feature

A longer description about this new feature and all it's
wonderful new featurelets.
```

### Code Format

Please format code with [Black](https://black.readthedocs.io/en/stable/) formatter/convention.

NOTE: We must only use *relative* imports for importing within this codebase, due to the odd nature of the QGIS plugin environment.

### Dev tools virtual environment

Dev tools i.e. pytest are installed in a virtual environment, but we still need access to the global python environment to access QGIS's PyQGIS libraries. To do this, create the venv with additional access to system packages:

```bash
/bin/python -m venv --system-site-packages --upgrade-deps .venv
```

or replace `/bin/python` with the path to your Python installation used by QGIS.

Then activate the virtualenv, and install dev tools:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dev_requirements.txt
```

#### Updating dev tools

To update dev tools, edit `dev_requirements.in` with any changes needed, then use `pip-compile` to update the pinned versions, and finally upgrade the venv:

```bash
pip-compile requirements_dev.in
python -m pip install --upgrade -r dev_requirements.txt
```