def classFactory(iface):
    from .netcdf_viewer import NetCDFViewer
    return NetCDFViewer(iface)
