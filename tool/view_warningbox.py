from typing import Literal

from PyQt5.QtWidgets import QMessageBox
from .model.network import Node


def show_node_consolidation_warning(
    a_or_b: Literal["A", "B"], node: Node, other_node: Node
) -> bool:
    """
    This is a popup warning box shown to users when they try to consolidate a node that
    has already been consolidated in a different comparison.

    Returns True/False, True if the user clicks OK, False if Cancel.

    This totally breaks the MVVM / MVC pattern we're using, but it works.
    """
    user_says_ok = False

    msg = QMessageBox()
    msg.setModal(True)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle(f"Node {a_or_b} {node.name} already consolidated")
    msg.setInformativeText(
        (
            f"The node in Network {a_or_b}:\n\n"
            + f"{node.name} (id = {node.id})\n\n"
            + "has already been marked as the same as another node:\n\n"
            + f"{other_node.name} (id = {other_node.id})).\n\n"
            + " If you mark  this node as the same instead, this will"
            + " override your previous match.\n"
            + "Are you sure?"
        )
    )
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
