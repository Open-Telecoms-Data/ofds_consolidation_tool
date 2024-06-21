from pathlib import Path

# Paths to resources

PLUGIN_DIR = Path(__file__).resolve().parent

STYLESHEETS_DIR = PLUGIN_DIR / "tool" / "stylesheets"

STYLESHEET_NODES = STYLESHEETS_DIR / "networkProviderNodesMultiplePlainOutput.qml"
STYLESHEET_SPANS = STYLESHEETS_DIR / "networkProviderSpansMultiplePlainOutput.qml"
