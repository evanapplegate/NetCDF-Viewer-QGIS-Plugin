from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                    QTreeWidget, QTreeWidgetItem, QPushButton,
                                    QLabel, QComboBox, QSpinBox, QGroupBox, QCheckBox,
                                    QTextEdit)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog
from qgis.gui import QgsMessageBar
import numpy as np
import traceback
from osgeo import osr, gdal
import os

class NetCDFViewerDialog(QDialog):
    def __init__(self, iface, file_path):
        try:
            super().__init__(None)  # Set parent to None to make it a top-level window
            QgsMessageLog.logMessage(f"Initializing dialog with file: {file_path}", "NetCDF Viewer", level=0)
            self.iface = iface
            self.file_path = file_path
            
            # Load the dataset
            QgsMessageLog.logMessage("Opening NetCDF dataset...", "NetCDF Viewer", level=0)
            import netCDF4 as nc
            self.dataset = nc.Dataset(file_path)
            QgsMessageLog.logMessage("Dataset opened successfully", "NetCDF Viewer", level=0)
            
            # Setup UI
            self.setupUi()
            self.populateMetadata()
            self.populateTree()
            
            # Make sure dialog stays on top
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in initialization: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            raise

    def setupUi(self):
        """Set up the user interface."""
        try:
            QgsMessageLog.logMessage("Setting up UI...", "NetCDF Viewer", level=0)
            
            # Main layout
            layout = QVBoxLayout()
            self.setLayout(layout)
            
            # Add metadata text area
            metadata_group = QGroupBox("NetCDF Metadata")
            metadata_layout = QVBoxLayout()
            metadata_group.setLayout(metadata_layout)
            
            self.metadata_text = QTextEdit()
            self.metadata_text.setReadOnly(True)
            self.metadata_text.setMinimumHeight(200)  # Make it reasonably tall
            metadata_layout.addWidget(self.metadata_text)
            
            layout.addWidget(metadata_group)
            
            # Variable selection group
            var_group = QGroupBox("Variable Selection")
            var_layout = QVBoxLayout()
            var_group.setLayout(var_layout)
            
            # Tree view for dimensions and variables
            self.tree = QTreeWidget()
            self.tree.setHeaderLabels(["Name", "Details"])
            self.tree.setMinimumHeight(200)
            var_layout.addWidget(self.tree)
            
            # Combo box for variable selection
            self.var_combo = QComboBox()
            var_layout.addWidget(self.var_combo)
            
            # Visualize button
            self.visualize_btn = QPushButton("Visualize")
            self.visualize_btn.clicked.connect(self.visualize)
            var_layout.addWidget(self.visualize_btn)
            
            layout.addWidget(var_group)
            
            # Set window properties
            self.setWindowTitle(f"NetCDF Viewer - {os.path.basename(self.file_path)}")
            self.resize(600, 800)  # Make the window larger
            
            QgsMessageLog.logMessage("UI setup complete", "NetCDF Viewer", level=0)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in setupUi: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            raise

    def populateMetadata(self):
        """Populate the metadata text area with NetCDF global and variable attributes."""
        try:
            metadata = []
            
            # Global attributes
            metadata.append("=== Global Attributes ===")
            for attr in self.dataset.ncattrs():
                value = getattr(self.dataset, attr)
                metadata.append(f"{attr}: {value}")
            metadata.append("")
            
            # Dimensions
            metadata.append("=== Dimensions ===")
            for dim_name, dim in self.dataset.dimensions.items():
                metadata.append(f"{dim_name}: {len(dim)}")
            metadata.append("")
            
            # Variables
            metadata.append("=== Variables ===")
            for var_name, var in self.dataset.variables.items():
                metadata.append(f"\nVariable: {var_name}")
                metadata.append(f"  Shape: {var.shape}")
                metadata.append(f"  Dimensions: {var.dimensions}")
                metadata.append(f"  Type: {var.dtype}")
                
                # Variable attributes
                if var.ncattrs():
                    metadata.append("  Attributes:")
                    for attr in var.ncattrs():
                        value = getattr(var, attr)
                        metadata.append(f"    {attr}: {value}")
            
            # Special handling for projection info
            proj_vars = ['crs', 'transverse_mercator', 'projection', 'lambert_conformal_conic',
                        'goes_imager_projection', 'polar_stereographic', 'grid_mapping']
            
            for var_name in proj_vars:
                if var_name in self.dataset.variables:
                    metadata.append(f"\n=== Projection Information ({var_name}) ===")
                    proj_var = self.dataset.variables[var_name]
                    for attr in proj_var.ncattrs():
                        value = getattr(proj_var, attr)
                        metadata.append(f"{attr}: {value}")
            
            # Set the text
            self.metadata_text.setPlainText('\n'.join(metadata))
            QgsMessageLog.logMessage("Metadata populated", "NetCDF Viewer", level=0)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in populateMetadata: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            raise

    def populateTree(self):
        try:
            QgsMessageLog.logMessage("Populating tree...", "NetCDF Viewer", level=0)
            # Add dimensions
            dim_root = QTreeWidgetItem(self.tree, ["Dimensions"])
            for dim_name, dim in self.dataset.dimensions.items():
                QgsMessageLog.logMessage(f"Adding dimension: {dim_name}", "NetCDF Viewer", level=0)
                item = QTreeWidgetItem(dim_root, [
                    dim_name,
                    str(len(dim))
                ])
            
            # Add variables
            var_root = QTreeWidgetItem(self.tree, ["Variables"])
            for var_name, var in self.dataset.variables.items():
                QgsMessageLog.logMessage(f"Adding variable: {var_name}", "NetCDF Viewer", level=0)
                item = QTreeWidgetItem(var_root, [
                    var_name,
                    str(var.shape)
                ])
                self.var_combo.addItem(var_name)
            
            self.tree.expandAll()
            QgsMessageLog.logMessage("Tree populated", "NetCDF Viewer", level=0)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in populateTree: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            raise

    def get_projection_info(self):
        """Extract projection information from NetCDF file."""
        # Common projection variable names
        proj_vars = ['crs', 'transverse_mercator', 'projection', 'lambert_conformal_conic',
                    'goes_imager_projection', 'polar_stereographic', 'grid_mapping']
        
        # Try to find projection variable
        proj_var = None
        for var_name in proj_vars:
            if var_name in self.dataset.variables:
                proj_var = self.dataset.variables[var_name]
                break
        
        if proj_var is None:
            return None, None
        
        # Get all projection attributes
        proj_attrs = {attr: getattr(proj_var, attr) for attr in proj_var.ncattrs()}
        QgsMessageLog.logMessage(f"Found projection attributes: {proj_attrs}", "NetCDF Viewer", level=0)
        
        # Try to create projection string based on attributes
        srs = osr.SpatialReference()
        
        # Check for common projection types
        if 'grid_mapping_name' in proj_attrs:
            mapping_name = proj_attrs['grid_mapping_name']
            
            if mapping_name == 'latitude_longitude':
                srs.ImportFromEPSG(4326)
            
            elif mapping_name == 'transverse_mercator':
                srs.SetTM(
                    proj_attrs.get('latitude_of_projection_origin', 0),
                    proj_attrs.get('longitude_of_central_meridian', 0),
                    proj_attrs.get('scale_factor_at_central_meridian', 1),
                    proj_attrs.get('false_easting', 0),
                    proj_attrs.get('false_northing', 0)
                )
            
            elif mapping_name == 'lambert_conformal_conic':
                srs.SetLCC(
                    proj_attrs.get('standard_parallel_1', 30),
                    proj_attrs.get('standard_parallel_2', 60),
                    proj_attrs.get('latitude_of_projection_origin', 0),
                    proj_attrs.get('longitude_of_central_meridian', 0),
                    proj_attrs.get('false_easting', 0),
                    proj_attrs.get('false_northing', 0)
                )
            
            elif mapping_name == 'geostationary':
                srs.ImportFromProj4(
                    f"+proj=geos +h={proj_attrs.get('perspective_point_height', 0)} " +
                    f"+lon_0={proj_attrs.get('longitude_of_projection_origin', 0)} " +
                    "+datum=WGS84 +units=m +no_defs"
                )
            
            elif mapping_name == 'polar_stereographic':
                srs.SetPS(
                    proj_attrs.get('latitude_of_projection_origin', 90),
                    proj_attrs.get('longitude_of_projection_origin', 0),
                    proj_attrs.get('scale_factor', 1),
                    proj_attrs.get('false_easting', 0),
                    proj_attrs.get('false_northing', 0)
                )
        
        # Try to get the variable name safely
        try:
            var_name = getattr(proj_var, 'name', None)
        except:
            var_name = None
            
        return srs, var_name

    def get_geotransform(self, var):
        """Extract geotransform information from variable coordinates."""
        try:
            # Get dimension names
            dims = var.dimensions
            
            # Look for coordinate variables
            x_var = y_var = None
            x_name = y_name = None
            
            # Common names for x/y coordinates
            x_coords = ['x', 'lon', 'longitude', 'projection_x_coordinate']
            y_coords = ['y', 'lat', 'latitude', 'projection_y_coordinate']
            
            # Try to get coordinates from variable attributes first
            if hasattr(var, 'coordinates'):
                coord_vars = var.coordinates.split()
                for coord_name in coord_vars:
                    if coord_name in self.dataset.variables:
                        coord_var = self.dataset.variables[coord_name]
                        if coord_name in x_coords or (hasattr(coord_var, 'axis') and getattr(coord_var, 'axis') == 'X'):
                            x_var = coord_var
                            x_name = coord_name
                        elif coord_name in y_coords or (hasattr(coord_var, 'axis') and getattr(coord_var, 'axis') == 'Y'):
                            y_var = coord_var
                            y_name = coord_name
            
            # If not found in coordinates, try dimensions
            if x_var is None or y_var is None:
                for dim in dims:
                    if dim in self.dataset.variables:
                        coord_var = self.dataset.variables[dim]
                        if dim in x_coords or (hasattr(coord_var, 'axis') and getattr(coord_var, 'axis') == 'X'):
                            x_var = coord_var
                            x_name = dim
                        elif dim in y_coords or (hasattr(coord_var, 'axis') and getattr(coord_var, 'axis') == 'Y'):
                            y_var = coord_var
                            y_name = dim
            
            if x_var is not None and y_var is not None:
                x = x_var[:]
                y = y_var[:]
                
                # Handle different array orientations
                if len(x.shape) > 1:
                    x = x[0, :]  # Take first row for 2D coordinates
                if len(y.shape) > 1:
                    y = y[:, 0]  # Take first column for 2D coordinates
                
                # Check if coordinates are in ascending order
                x_ascending = x[1] > x[0] if len(x) > 1 else True
                y_ascending = y[1] > y[0] if len(y) > 1 else True
                
                # Check if we're dealing with GOES satellite data (coordinates in radians)
                is_goes = False
                if 'goes_imager_projection' in self.dataset.variables:
                    is_goes = True
                    # Get satellite height for scaling
                    proj_var = self.dataset.variables['goes_imager_projection']
                    satellite_height = getattr(proj_var, 'perspective_point_height', 35786023.0)  # Default GOES-R height
                    
                    # Convert coordinates from radians to meters
                    x = x * satellite_height
                    y = y * satellite_height
                    QgsMessageLog.logMessage(f"Converting GOES coordinates using satellite height: {satellite_height}m", "NetCDF Viewer", level=0)
                
                # Get pixel sizes
                pixel_width = abs(x[1] - x[0]) if len(x) > 1 else 1
                pixel_height = abs(y[1] - y[0]) if len(y) > 1 else 1
                
                # Get corners
                x_min = float(x[0])
                if not x_ascending:
                    x_min = float(x[-1])
                    pixel_width = -pixel_width
                
                y_max = float(y[0])  # Use first Y as top edge
                if y_ascending:
                    y_max = float(y[-1])  # If ascending, use last Y as top edge
                    pixel_height = -pixel_height  # Negative height for ascending Y
                
                # Create geotransform: (top_left_x, pixel_width, x_rotation, top_left_y, y_rotation, pixel_height)
                geotransform = [
                    x_min,           # Left edge
                    pixel_width,     # Pixel width
                    0,              # X rotation
                    y_max,           # Top edge
                    0,              # Y rotation
                    -pixel_height    # Pixel height (negative for north-up images)
                ]
                
                QgsMessageLog.logMessage(
                    f"Coordinate details:\n" +
                    f"X: min={x[0]}, max={x[-1]}, ascending={x_ascending}\n" +
                    f"Y: min={y[0]}, max={y[-1]}, ascending={y_ascending}\n" +
                    f"Is GOES: {is_goes}\n" +
                    f"Geotransform: {geotransform}",
                    "NetCDF Viewer", level=0
                )
                
                return geotransform, (x_name, y_name)
            
            return None, None
        except Exception as e:
            QgsMessageLog.logMessage(f"Error getting geotransform: {str(e)}", "NetCDF Viewer", level=2)
            return None, None

    def visualize(self):
        try:
            QgsMessageLog.logMessage("Visualizing...", "NetCDF Viewer", level=0)
            var_name = self.var_combo.currentText()
            if not var_name:
                return
                
            var = self.dataset.variables[var_name]
            QgsMessageLog.logMessage(f"Selected variable: {var_name}, shape: {var.shape}, dtype: {var.dtype}", "NetCDF Viewer", level=0)
            QgsMessageLog.logMessage(f"Variable dimensions: {var.dimensions}", "NetCDF Viewer", level=0)
            
            # Check if variable has valid dimensions for a raster
            if len(var.shape) < 2:
                self.iface.messageBar().pushMessage(
                    "Error", f"Variable {var_name} must have at least 2 dimensions for visualization", level=2)
                return
            
            # Create a temporary file for visualization
            import tempfile
            import os
            import numpy as np
            
            # Create temp file with .tif extension (not .tiff)
            temp_handle, temp_tif = tempfile.mkstemp(suffix='.tif')
            os.close(temp_handle)  # Close the file handle
            
            QgsMessageLog.logMessage(f"Creating temporary file: {temp_tif}", "NetCDF Viewer", level=0)
            
            # Get data and handle fill values
            data = var[:]
            fill_value = None
            if hasattr(var, '_FillValue'):
                fill_value = float(var._FillValue)  # Convert to float
            elif hasattr(var, 'missing_value'):
                fill_value = float(var.missing_value)  # Convert to float
            else:
                fill_value = -9999.0  # Default float fill value
            
            # Apply scale and offset if they exist
            scale_factor = float(getattr(var, 'scale_factor', 1.0))
            add_offset = float(getattr(var, 'add_offset', 0.0))
            
            # Convert data to float32 for visualization
            data = data.astype(np.float32)
            if fill_value is not None:
                data = np.ma.masked_equal(data, fill_value)
                # Update fill value for scaled data
                fill_value = fill_value * scale_factor + add_offset
            data = data * scale_factor + add_offset
            
            # Create output raster
            driver = gdal.GetDriverByName('GTiff')
            if driver is None:
                raise RuntimeError("Failed to get GTiff driver")
                
            # Get dimensions
            xsize = int(data.shape[1])  # Width
            ysize = int(data.shape[0])  # Height
            
            QgsMessageLog.logMessage(f"Creating raster with dimensions: {xsize}x{ysize}", "NetCDF Viewer", level=0)
            
            # Create with options
            creation_options = ['COMPRESS=LZW', 'TILED=YES']
            out_ds = driver.Create(temp_tif, xsize, ysize, 1, gdal.GDT_Float32, creation_options)
            
            if out_ds is None:
                raise RuntimeError(f"Failed to create output dataset at {temp_tif}")
            
            # Get projection information
            srs, grid_mapping = self.get_projection_info()
            if srs:
                QgsMessageLog.logMessage(f"Setting projection: {srs.ExportToWkt()}", "NetCDF Viewer", level=0)
                out_ds.SetProjection(srs.ExportToWkt())
            
            # Get geotransform information
            geotransform, coord_names = self.get_geotransform(var)
            if geotransform:
                QgsMessageLog.logMessage(f"Setting geotransform: {geotransform}", "NetCDF Viewer", level=0)
                out_ds.SetGeoTransform(geotransform)
            
            # Write data
            band = out_ds.GetRasterBand(1)
            if band is None:
                raise RuntimeError("Failed to get raster band")
                
            write_status = band.WriteArray(data)
            if write_status != 0:
                raise RuntimeError(f"Failed to write array to band: {write_status}")
                
            if fill_value is not None:
                QgsMessageLog.logMessage(f"Setting no data value: {fill_value}", "NetCDF Viewer", level=0)
                try:
                    band.SetNoDataValue(float(fill_value))
                except Exception as e:
                    QgsMessageLog.logMessage(f"Warning: Could not set no data value: {str(e)}", "NetCDF Viewer", level=1)
            
            # Compute statistics for better visualization
            band.ComputeStatistics(False)
            
            # Close dataset to flush to disk
            band = None
            out_ds = None
            
            # Load as raster layer
            layer_name = f"{var_name} from {os.path.basename(self.file_path)}"
            QgsMessageLog.logMessage(f"Creating raster layer: {layer_name}", "NetCDF Viewer", level=0)
            
            layer = QgsRasterLayer(temp_tif, layer_name)
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                QgsMessageLog.logMessage("Layer added successfully", "NetCDF Viewer", level=0)
            else:
                error = layer.error().summary()
                QgsMessageLog.logMessage(f"Layer is invalid. Error: {error}", "NetCDF Viewer", level=2)
                self.iface.messageBar().pushMessage(
                    "Error", f"Failed to create layer: {error}", level=2)
            
            QgsMessageLog.logMessage("Visualization complete", "NetCDF Viewer", level=0)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in visualize: {str(e)}\n{traceback.format_exc()}", "NetCDF Viewer", level=2)
            self.iface.messageBar().pushMessage("Error", str(e), level=2)
            raise
