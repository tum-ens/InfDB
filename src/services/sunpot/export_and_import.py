from src.services.sunpot.exporter import export_to_csv
from src.services.sunpot.importer import import_to_v5

print("exporting citydb v4 solar potential calculations to csv")
export_to_csv()
print("export succesfull")

print("importing solarpotential calculations to v5")
import_to_v5()
print("import succesfull")
