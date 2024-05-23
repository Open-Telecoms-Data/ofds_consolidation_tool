import logging

from pathlib import Path
from typing import Sequence, Union
from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5 import QtCore

from .model.qgis import write_geojson_from_features

from .model.network import Feature


logger = logging.getLogger(__name__)


def save_file_dialog(file_extension: str) -> Union[str, None]:
    options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    options |= QFileDialog.DontUseCustomDirectoryIcons
    dialog = QFileDialog()
    dialog.setOptions(options)

    dialog.setFilter(dialog.filter() | QtCore.QDir.Hidden)

    # dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setFileMode(QFileDialog.AnyFile)

    dialog.setAcceptMode(QFileDialog.AcceptSave)

    dialog.setDefaultSuffix(file_extension)
    dialog.setNameFilters([f"{file_extension} (*.{file_extension})"])

    if dialog.exec_() == QDialog.Accepted:
        path = dialog.selectedFiles()[0]  # returns a list
        return path
    else:
        return None


def save_geojson_file_dialog(features: Sequence[Feature]):
    logger.info("Opening File Save Dialog for GeoJSON")
    file_path = save_file_dialog(file_extension="geojson")
    logger.info(f"Saving GeoJSON to '{file_path}'")
    if file_path:
        with Path(file_path).open("w", encoding="utf-8") as f:
            write_geojson_from_features(f, features)
