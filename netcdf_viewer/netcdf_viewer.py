import os
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsRasterLayer, QgsMessageLog
import netCDF4 as nc
from .netcdf_viewer_dialog import NetCDFViewerDialog
import traceback

class NetCDFViewer:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'NetCDF Viewer'
        self.dialog = None
        
        # Create toolbar
        self.toolbar = None
        self.setup_toolbar()

    def setup_toolbar(self):
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar('NetCDF Viewer')
            self.toolbar.setObjectName('NetCDF Viewer')

    def add_action(self, icon_path, text, callback):
        icon = QIcon(icon_path)
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(True)
        
        if self.toolbar:
            self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text='NetCDF Viewer',
            callback=self.run
        )

    def unload(self):
        try:
            # Remove menu items and toolbar icons
            for action in self.actions:
                self.iface.removePluginMenu(self.menu, action)
                self.iface.removeToolBarIcon(action)
            self.actions = []

            # Remove toolbar if it exists
            if hasattr(self, 'toolbar') and self.toolbar:
                del self.toolbar
                self.toolbar = None

            # Close dialog if it exists
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.close()
                self.dialog = None

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in unload: {str(e)}", "NetCDF Viewer", level=2)

    def run(self):
        try:
            QgsMessageLog.logMessage("Starting NetCDF Viewer plugin...", "NetCDF Viewer", level=0)
            # Show file dialog to select NetCDF file
            file_path, _ = QFileDialog.getOpenFileName(None, "Select NetCDF File", "", "NetCDF Files (*.nc)")
            if not file_path:
                return
            
            QgsMessageLog.logMessage(f"Selected file: {file_path}", "NetCDF Viewer", level=0)
            
            # Create and show the dialog
            if self.dialog:
                self.dialog.close()
                self.dialog = None
            
            self.dialog = NetCDFViewerDialog(self.iface, file_path)
            self.dialog.show()
            
            QgsMessageLog.logMessage("Dialog shown successfully", "NetCDF Viewer", level=0)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in run: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            self.iface.messageBar().pushMessage("Error", str(e), level=2)
