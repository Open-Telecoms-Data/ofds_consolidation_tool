#!/bin/bash
set -euo pipefail

NEW_VERSION="${NEW_VERSION:?Error: NEW_VERSION not set}"

# Update metadata.txt with the new version
jinja2 --strict -D new_version="${NEW_VERSION}" templates/.metadata.txt.j2 > metadata.txt

# Create a QGIS-compatible Plugin and
# Copy our files into the plugin dir.
# Note the directory name must not conflict with other plugins.

ZIPDIR="dist/ofds_consolidation_tool/"

# Check we won't accidentally overwrite stuff
if [ -d "$ZIPDIR" ]; then
  echo "Error: temporary directory already exists. Are you sure you're running this in project root?"
  exit 1
fi

# Make our dist dir if it doesn't exist
mkdir -p "$ZIPDIR"

# Clean up __pycache__ and .pyc files
pyclean . || true


# Copy in relevant files
cp -r \
  "metadata.txt" \
  "README.md" \
  "LICENSE" \
  "docs/" \
  "pyproject.toml" \
  "tests/" \
  "dev_requirements.in" \
  "dev_requirements.txt" \
  "tool/" \
  "gui.py" \
  "gui_style.py" \
  "helpers.py" \
  "ofds.py" \
  "plugin.py" \
  "resources.py" \
  "$ZIPDIR"

pushd dist/
# Create the Zip
zip -r "OFDS_Consolidation_Tool_QGIS_Plugin_v${NEW_VERSION}.zip" ofds_consolidation_tool/

# Clean up temporary dir
rm -r ofds_consolidation_tool/
popd
