#!/bin/bash
set -euo pipefail

pyuic5 gui.ui -o gui.py
pyuic5 gui_style.ui -o gui_style.py
