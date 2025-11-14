import pandas as pd
from sqlalchemy import create_engine, text
import os
import numpy as np
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from conexion.conexion import CargadorDatos

#Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..','..', 'datos', 'procesados')

#Directorio de entrada
directorioEntrada = os.path.join(directorio, 'df.csv')

#Carga de csv
df = pd.read_csv(directorioEntrada, encoding='windows-1252', on_bad_lines='skip')
engine = create_engine('mysql+mysqlconnector://root:5514@localhost/partidosBD')

#Strptime
#df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce').dt.date

#Primer intentoformato con año de 2 dígitos
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce')

df['Date'] = df['Date'].apply(lambda x: x.isoformat() if x is not None else None)
#dftest = df['Date']
#print(dftest)

#Insertar los equipos
equipos = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())
equipos_df = pd.DataFrame({'nombre_equipo': equipos})

with engine.begin() as conn:
    for nombre_equipo in equipos_df['nombre_equipo']:
        conn.execute(
            text("INSERT IGNORE INTO EquiposRef (nombre_equipo) VALUES (:nombre_equipo)"),
            {'nombre_equipo': nombre_equipo}
        )

#Mapear los nombres de equipos a sus IDs
equipos_ref = pd.read_sql('SELECT id_equipo, nombre_equipo FROM EquiposRef', engine)
nombre_to_id = dict(zip(equipos_ref['nombre_equipo'], equipos_ref['id_equipo']))

#IDS en el dataframe
df['id_equipo_local'] = df['HomeTeam'].map(nombre_to_id)
df['id_equipo_visitante'] = df['AwayTeam'].map(nombre_to_id)

#reemplazar NaN por None
df = df.astype(str).replace({'nan': None, 'None': None})
df = df.where(pd.notnull(df), None)

# Reemplazar NaT o NaN por None antes de insertar
df['Date'] = df['Date'].replace({pd.NaT: None, 'NaT': None, np.nan: None})
df['Time'] = df['Time'].replace({pd.NaT: None, 'NaT': None, np.nan: None})

#Insertar los datos en la tablisima
cargador = CargadorDatos()

# Mapear las columnas CSV a nombres de BD
mapeo_columnas = {
    'Date': 'fecha',
    'Time': 'hora',
    'HomeTeam': 'equipo_local',
    'AwayTeam': 'equipo_visitante',
    'FTHG': 'goles_local_final',
    'FTAG': 'goles_visitante_final',
    'FTR': 'resultado_final',
    'HTHG': 'goles_local_ht',
    'HTAG': 'goles_visitante_ht',
    'HTR': 'resultado_ht',
    'HS': 'disparos_local',
    'AS': 'disparos_visitante',
    'HST': 'disparos_porteria_local',
    'AST': 'disparos_porteria_visitante',
    'HC': 'corners_local',
    'AC': 'corners_visitante',
    'HF': 'faltas_local',
    'AF': 'faltas_visitante',
    'HY': 'amarillas_local',
    'AY': 'amarillas_visitante',
    'HR': 'rojas_local',
    'AR': 'rojas_visitante'
}

df = df.rename(columns=mapeo_columnas)


df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
df['id_equipo_local'] = df['id_equipo_local'].astype('Int64')
df['id_equipo_visitante'] = df['id_equipo_visitante'].astype('Int64')
cargador.insertar_sin_duplicados(df, 'PartidosML')

        
