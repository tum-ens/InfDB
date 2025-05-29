# Load LOD2 (building data)
from src.services.loader.sources import basemap, bkg, census2022, lod2, plz

lod2.imp_lod2()

# # Load BKG
bkg.import_bkg()

# # Load Census2022
census2022.import_census2022()

# # Load Basemap
basemap.import_basemap()

# # Load Zip Codes
plz.import_plz()
