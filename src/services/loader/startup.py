# Load LOD2 (building data)
from src.services.loader import imp_basemap, imp_bkg, imp_census2022, imp_lod2, imp_plz

imp_lod2.imp_lod2()

# # Load BKG
imp_bkg.import_bkg()

# # Load Census2022
imp_census2022.import_census2022()

# # Load Basemap
imp_basemap.import_basemap()

# # Load Zip Codes
imp_plz.import_plz()
