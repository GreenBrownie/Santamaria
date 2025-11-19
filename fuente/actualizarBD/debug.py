import pandas as pd
import os
from datetime import datetime

#Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..', '..', 'datos')

# Datos originales
directorioOriginales= os.path.join(directorio, 'originales')

#Lista para almacenar los DataFrames
dataframes = []

# Procesar calendario
tmp16 = pd.read_csv(os.path.join(directorioOriginales, 'E0(24).csv'), encoding='windows-1252', on_bad_lines='skip')

# Procesar calendario
tmp17 = pd.read_csv(os.path.join(directorioOriginales, 'E0(25).csv'), encoding='windows-1252', on_bad_lines='skip')

print(type(tmp16['Date'][0]))
print(type(tmp17['Date'][0]))

print((tmp16['Date'][0]))
print((tmp17['Date'][0]))