#!/bin/bash
set -euo pipefail

exec env QGIS_DEBUG=9 QGIS_LOG_FILE=/tmp/qgis.log qgis