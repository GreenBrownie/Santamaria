import pandas as pd
from sqlalchemy import create_engine, text
import os
import numpy as np

#Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..', 'recopilacion', 'archivos')

#Ruta del archivo CSV
ruta_archivo = os.path.join(directorio, 'df.csv')

#Carga de csv
df = pd.read_csv(ruta_archivo, encoding='windows-1252', on_bad_lines='skip')

engine = create_engine('mysql+mysqlconnector://root:5514@localhost/partidosBD')

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

#Insertar los datos en la tablisima
with engine.begin() as conn:
    for _, row in df.iterrows():
        conn.execute(
            text("""
                INSERT INTO PartidosML (
                    fecha, hora, equipo_local, equipo_visitante, id_equipo_local, id_equipo_visitante, goles_local_final, goles_visitante_final, resultado_final, goles_local_ht, goles_visitante_ht, resultado_ht, disparos_local, disparos_visitante, disparos_porteria_local, disparos_porteria_visitante, corners_local, corners_visitante, faltas_local, faltas_visitante, amarillas_local, amarillas_visitante, rojas_local, rojas_visitante
                ) VALUES (
                    :Date, :Time, :HomeTeam, :AwayTeam, :id_equipo_local, :id_equipo_visitante, :FTHG, :FTAG, :FTR, :HTHG, :HTAG, :HTR, :HS, :AS, :HST, :AST, :HC, :AC, :HF, :AF, :HY, :AY, :HR, :AR
                )
            """),
            row.to_dict()
        )
