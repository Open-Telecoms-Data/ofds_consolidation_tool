from typing import Literal

from PyQt5.QtWidgets import QMessageBox
from .model.network import Node


def show_node_multi_consolidation_warning(
    a_or_b: Literal["A", "B"], node: Node, other_node: Node
) -> bool:
    """
    This is a popup warning box shown to users when they try to consolidate a node that
    has already been consolidated in a different comparison.

    Returns True/False, True if the user clicks OK, False if Cancel.

    This totally breaks the MVVM / MVC pattern we're using, but it works.
    """
    title = f"Node {a_or_b} {node.name} already consolidated"
    info_text = (
        f"The node in Network {a_or_b}:\n\n"
        + f"{node.name} (id = {node.id})\n\n"
        + "has already been marked as the same as another node:\n\n"
        + f"{other_node.name} (id = {other_node.id})).\n\n"
        + " If you mark  this node as the same instead, this will"
        + " override your previous match.\n"
        + "Are you sure?"
    )

    return show_warningbox(title, info_text)


def show_node_incomplete_consolidation_warning() -> bool:
    title = "Warning: Not all Node comparisons have been marked"
    info_text = (
        "Not all Node comparisons have been marked as the same or not the same.\n"
        + "If you continue, all remaining node comparisons will be marked as "
        + "Not the Same, and you will move on to comparing spans.\n\n"
        + "Are you sure you wish to finish comparing nodes?"
    )

    return show_warningbox(title, info_text, icon=QMessageBox.Icon.Warning)


def show_warningbox(
    title: str, info_text: str, icon: QMessageBox.Icon = QMessageBox.Icon.Question
) -> bool:
    """
    This function shows a popup warning to the user, with the given title and info text,
    and OK / Cancel buttons.

    Returns True/False, True if the user clicks OK, False if Cancel.
    """

    user_says_ok = False

    msg = QMessageBox()
    msg.setModal(True)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setInformativeText(info_text)
    msg.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
    )

    def _btn_clicked(btn):
        nonlocal user_says_ok
        if btn.text() == "OK":
            user_says_ok = True
        else:
            user_says_ok = False

    msg.buttonClicked.connect(_btn_clicked)

    msg.exec_()

    return user_says_ok
