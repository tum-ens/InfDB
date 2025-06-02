--------------------------------------
QGIS Web Client Documentation for ENS:
--------------------------------------

We use the docker images of the QGIS Web Client (QWC) and qwc-services
for visualization of geodata from the 3DCityDB. Once QWC is set up on
the server, one can (after some local configurations) create QGIS
projects on a local machine with QGIS Desktop and upload them to the
server. The server generates a “theme” from every added project and
makes it visible on a web interface.

| The official documentation for QWC can be found at
| https://qwc-services.github.io/master/

| The respective GitHub repo can be found at
| https://github.com/qwc-services/qwc-docker

| After installation, the QWC interface can be reached via
| http://10.162.28.86:8088/

| And the admin interface can be reached via
| http://10.162.28.86:8088/qwc_admin/

-------------
Useful Files:
-------------

In the folder of this documentation, two additional files can be found.
These are sample config files.

1. **pg_service.conf:**

This file contains two service definitions. A service definition
contains all connection details needed to connect to a specific database
(host, port, database name, username, password, if SSL is to be used)
and summarizes them under a single name (the service name). In QGIS
layer definitions, a database can be addressed by a service name,
erasing the need to add all connection details to every single layer.
The service name can also be seen as proxy for the connection details,
as it allows to change the connection details by editing the
pg_service.conf without having to edit the layers. The concept of
service files is also described here:
`https://docs.qgis.org/3.34/en/docs/user_manual/managing_data_source/opening_data.html#postgresql-service-connection-file <https://docs.qgis.org/3.34/en/docs/user_manual/managing_data_source/opening_data.html%23postgresql-service-connection-file>`__

The sample file is a modified version of the config file in the GitHub
repo
(https://github.com/qwc-services/qwc-docker/blob/master/pg_service.conf).
It contains one service definition for the config database
(qwc_configdb) that contains internal values of QWC. This definition is
unchanged from the repo.

The other service definition is for the geodatabase that contains
spatial data (qwc_geodb). This definition was adjusted in comparison to
the repo. When connection details of the geodatabase change (e.g. by
moving to another server), this definition must be updated.

2. **themesConfig.json**

This file contains config parameters that define how QWC generates
themes from the uploaded QGIS project files. A theme is a visualization
of a QGIS project on the QWC server and it is generated from the project
file itself in combination with the config parameters defined here.
Config parameters can be settings for specific themes (project files) or
default values for all themes (project files). They include for example
the background layer of a theme.

The sample file is a modified version of the config file in the GitHub
repo
(https://github.com/qwc-services/qwc-docker/blob/master/volumes/config-in/default/themesConfig.json).
A complete manual to configure themes including a table with all
possible config parameters can be found at
`https://qwc-services.github.io/master/configuration/ThemesConfiguration/#configuring-the-themes-in-themesconfigjson <https://qwc-services.github.io/master/configuration/ThemesConfiguration/%23configuring-the-themes-in-themesconfigjson>`__.

----------------------
Server configurations:
----------------------

**Install the QWC docker images:**

see https://qwc-services.github.io/master/QuickStart/

**Start/stop QWC with:**

| docker compose up –d
| docker compose down
| *(do not use „docker compose restart“, it may result in server
  errors)*

**Modify pg_service.conf (connect to 3DCity-DB):**\ *
(or copy sample file)*

| [qwc_geodb]
| host=10.162.28.86
| port=1230
| dbname=postgres
| user=postgres
| password=need
| sslmode=disable

**Replace /volumes/config-in/default/themesConfig.json:**\ *(see sample file)*

scp .\\themesConfig.json
student@10.162.28.86:~/qwc-docker/volumes/config-in/default/themesConfig.json

**Comment out lines in docker-compose.yml (deactivate default theme):**

| #-
  ./volumes/demo-data/setup-demo-data.sh:/docker-entrypoint-initdb.d/2_setup-demo-data.sh
| #-
  ./volumes/demo-data/setup-demo-data-permissions.sh:/tmp/extra-init.d/setup-demo-data-permissions.sh

**Add to docker-compose.yml (change project file format from .qgs to
.qgz):
**\ *(in the environment section of the qwc-qgis-server service)*

QGIS_PROJECT_SUFFIX: 'qgz'

**Add to /volumes/config-in/default/tenantConfig.json (change project
file format from .qgs to .qgz):
**\ *(in the toplevel config section)*

"qgis_project_extension": ".qgz"

---------------------
Local configurations:
---------------------

*(shown for Windows)*

**Add service configuration file pg_service.conf:
**\ *(e.g. under "C:\\Users\\JohnDoe\\pg_service.conf")
(save the file in UNIX format regarding EOL delimiter / use sample file)
(see*
https://docs.qgis.org/3.34/en/docs/user_manual/managing_data_source/opening_data.html#postgresql-service-connection-file\ *)*

| [qwc_geodb]
| host=10.162.28.86
| port=1230
| dbname=postgres
| user=postgres
| password=need
| sslmode=disable

**Add path to service configuration file to environment variable
PGSERVICEFILE:**

.. image:: ../img/add_environment_variable.png

**Connect to the database via service configuration:
**\ *(use LTS QGIS version 3.34.15 to be compatible with the QGIS server
image; see* https://download.qgis.org/downloads/\ *)*

|image1|\ |image2|

----------------
Publish project:
----------------

| **Create QGIS project and save it**
| *(Note: QWC uses .qgs files by default. We changed this setting to
  .qgz files because that is the default saving format of QGIS
  Desktop.)*

**Upload the project:**

scp .\\project.qgz
student@10.162.28.86:~/qwc-docker/volumes/qgs-resources/scan/project.qgz

**Open admin webinterface and log in:
**\ *(address: http://10.162.28.86:8088/qwc_admin/)
(username: admin, password: qgis-admin)*

.. image:: ../img/login_qwc_admin.png

**Generate service configuration:**

.. image:: ../img/generate_service_configuration.png

------------------------------------
Tips for working with QGIS projects:
------------------------------------

We recommend some methods to make the maintenance of QGIS projects
easier. For pylovo, there already exist two template project files in
the pylovo repo (https://github.com/tum-ens/pylovo/tree/main/QGIS). One
is for local use and its layers use hard-coded data sources, the other
is for use with QWC and its layers refer to a service definition as
described above. Apart from that the two files are identical. The
general maintenance techniques are described now:

1. **Dynamic styling with project variables**

When the styles of multiple layers use the same values (e.g. for
thickness of lines), it can make sense to define the value in a
project variable (*Project > Properties > Variables*) and then
reference the variable in the respective layers instead of hardcoding
the value in every layer. That makes it easier to change such style
values.

More on project variables can be found under
`https://docs.qgis.org/3.34/en/docs/user_manual/introduction/general_tools.html#storing-values-in-variables <https://docs.qgis.org/3.34/en/docs/user_manual/introduction/general_tools.html%23storing-values-in-variables>`__.

2. **Dynamic version filtering with project variables and virtual layers**

In pylovo, the database can contain data that was created with
different parameter sets, where each parameter set is identified by a
version_id. In the visualization, usually only one version of the
data shall be shown. To do so, one can again define a project
variable that contains the version_id of the data version that shall
currently be shown. The layers, whose source table contain different
versions, are then created as virtual layers. Virtual layers are
layers that are created by SQL queries based on existing layers or
database tables. These queries can also reference project variables
by *var(‘variable_name’).* A virtual layer is created via *Layer >
Create Layer > New Virtual Layer*. A query filtering for version_id
could look like this:

   SELECT \* FROM table_name WHERE version_id = var(‘version_id’)

More about virtual layers can be found under
`https://docs.qgis.org/3.40/en/docs/user_manual/managing_data_source/create_layers.html#creating-virtual-layers <https://docs.qgis.org/3.40/en/docs/user_manual/managing_data_source/create_layers.html%23creating-virtual-layers>`__.

3. **Dynamic data sources with service definitions**

By using a service definition file that contains a datasource (host,
port, database, user, password…) and referencing only the defined
service name instead of all connection details, changing data sources
becomes a lot easier, because only the service definition file has to
be changed. It is also useful because QWC also uses this service
definition approach and when you add the same service definition file
to your local machine as on the QWC server, you can upload and add
projects to QWC without changing data sources.

The service config file is described above under *Useful Files >
pg_service.conf* and the setup of the file and the layer data sources
on Windows are described above under *Local Configurations*.

.. |image1| image:: ../img/add_postgres_layer.png
.. |image2| image:: ../img/add_service_name.png
