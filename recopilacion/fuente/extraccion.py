import pandas as pd
import os

#Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..', 'archivos')

#Lista para almacenar los DataFrames
dataframes = []

#Iterar sobre los archivos en el directorio
for archivo in os.listdir(directorio):
    if archivo.endswith('.csv'):
        ruta_archivo = os.path.join(directorio, archivo)
        # Será necesario procesarlos en orden?
        print(f"Procesando {archivo}...")
        try:
            df = pd.read_csv(ruta_archivo, encoding='windows-1252', on_bad_lines='skip')
            dataframes.append(df)
        except Exception as e:
            print(f"Error {archivo}: {e}\n")


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

#Guardar el dataframe en un csv para testear
mega_df.to_csv(os.path.join(directorio, 'df.csv'), encoding='windows-1252', index=False)

        