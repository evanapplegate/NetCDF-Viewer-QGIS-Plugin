#!/bin/bash

# Remove old zip if it exists
rm -f netcdf_viewer.zip

# Create new zip
zip -r netcdf_viewer.zip netcdf_viewer

echo "ZIP file created successfully!"
