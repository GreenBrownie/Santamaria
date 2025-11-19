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
calendario_df = pd.read_csv(os.path.join(directorioOriginales, 'calendario.csv'), encoding='windows-1252', on_bad_lines='skip')
calendario_df.rename(columns={'Home Team': 'HomeTeam', 'Away Team': 'AwayTeam'}, inplace=True)

# Spurs y Man Utd en los datos usan nombres diferentes
calendario_df['HomeTeam'] = calendario_df['HomeTeam'].replace({'Spurs': 'Tottenham', 'Man Utd': 'Man United'})
calendario_df['AwayTeam'] = calendario_df['AwayTeam'].replace({'Spurs': 'Tottenham', 'Man Utd': 'Man United'})


# Separar fecha y hora
calendario_df[['Date', 'Time']] = calendario_df['Date'].str.split(' ', expand=True)

# Convertir fecha al formato 
calendario_df['Date'] = pd.to_datetime(calendario_df['Date'], format='%d/%m/%Y').dt.strftime('%d-%m-%Y')

calendario_df.to_csv(os.path.join(directorioOriginales, 'calendarioProc.csv'), encoding='windows-1252', index=False, mode='w') 
# Separar date y time

#Iterar sobre los archivos en el directorio
formatos = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']

for archivo in os.listdir(directorioOriginales):
    if archivo.endswith('.csv'):
        if archivo == 'calendario.csv':
            continue  # Ya procesado
        ruta_archivo = os.path.join(directorioOriginales, archivo)
        print(f"Procesando {archivo}...")
        try:
            df = pd.read_csv(ruta_archivo, encoding='windows-1252', on_bad_lines='skip')

            fecha = None
            for fmt in formatos:
                fecha = pd.to_datetime(df['Date'], format=fmt, errors='coerce')
                if fecha.notna().all():
                    break

            if fecha.isna().any():
                errores = df.loc[fecha.isna(), 'Date']
                raise ValueError(f"Fechas inválidas: {errores.size} en {archivo}")

            df['Date'] = fecha.dt.strftime('%Y-%m-%d')

            dataframes.append(df)

        except Exception as e:
            print(f"Error en {archivo}: {e}\n")

#Lista de columnas a seleccionar
columnas_seleccionadas = ['Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR','HS', 'AS', 'HST', 'AST', 'HC', 'AC','HF', 'AF', 'HY', 'AY', 'HR', 'AR']

#Limpiar y seleccionar columnas
dataframes_limpios = []
for df in dataframes:
    for col in columnas_seleccionadas:
        if col not in df.columns:
            df[col] = pd.NA
    df_limpio = df[columnas_seleccionadas]
    #Eliminar filas completamente vacías
    df_limpio = df_limpio.dropna(how='all')
    dataframes_limpios.append(df_limpio)

#Unir todos los DataFrames en uno solo
mega_df= pd.concat(dataframes_limpios)

#Directorio de salida
directorioSalida = os.path.join(directorio, 'procesados')

#Guardar el dataframe en un csv
mega_df.to_csv(os.path.join(directorioSalida, 'df.csv'), encoding='windows-1252', index=False, mode='w')
