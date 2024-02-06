from .plugin import OFDSDedupPlugin

def classFactory(iface):
    return OFDSDedupPlugin(iface)