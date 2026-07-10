---
icon: material/map-search
---
# Lizmap

## Configuration
# Preconditions:
1. The infdb database is up and running. (db profile in infdb.sh)
2. Lizmap web-instance is up and running. (lizmap profile in infdb.sh)

# In order to host a map on the lizmap web-instance using infdb, we have prepared a guideline of the necessary steps for the :
1. Download QGIS Desktop LTR (Long-Term-Release) from https://www.qgis.org/download/. 
2. In the QGIS Desktop app go into plugins and install the Lizmap plugin.
3. Open the Lizmap plugin and connect to the web-instance using it's URL.
4. Create a connection to infdb's PostgreSQL.
5. Create and save your project with the .qgs file extension. 
6. Open the Lizmap plugin and create the configuration file for the web-instance.
7. Create a subfolder for your project in the services/infdb-lizmap/lizmap/instances
8. Place both your .qgs project and the .qgs.cfg in the subfolder you created.
9. In the Lizmap web-instance go into Administration -> Maps management
10. Create a repository of the subfolder you created before.

# Tips and Tricks:
1. In the web-instance of Lizmap, there is the option to create groups and users, to distribute different rights. The Lizmap Plugin can see the groups and set specific rights for the project, based on the available groups such as admins, publishers, users, etc.
2. While creating the project in the Project Properties -> QGIS Server -> WFS/OAPIF you can set update, insert and delete rights for each layer.
3. In each layer's own Properties under Attributes Form, among other things, you can make fields uneditable, but visible. (useful for data collection)
4. In the Lizmap Plugin -> Layers, you can allow users to be able to click on an object in the web-instance and get data about it with the Popup checkbox.
5. In the Lizmap Plugin -> Attribute table & selection, you can also hide some fields from each layer.
6. In the Lizmap Plugin -> Layer Editing, you can give edit rights for each layer to specific user groups 
7. The writes from the Lizmap web-instance happen directly into the database, so a logging mechanism was created for one of the tables for which we allow data editing - see NEED-infdb/tools/infdb-basedata-buildings/sql/buildings_sql/16_logging _and_constraints_for_lizmap.sql

## License
Lizmap is released under the Mozilla Public License Version 2.0 (MPL-2.0), a weak copyleft Open Source license that allows for both open source and proprietary use with certain conditions.