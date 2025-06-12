from src.services.loader.sources import basemap, bkg, census2022, lod2, plz

# Load LOD2 (building data)
lod2.imp_lod2()

# Load BKG
bkg.import_bkg()

# Load Census2022
census2022.import_census2022()

# Load Zip Codes
plz.import_plz()

# Load Basemap
basemap.import_basemap()
