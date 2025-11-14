import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from conexion.conexion import CargadorDatos


def dict_equipos(cargador):
    query = "SELECT nombre_equipo, id_equipo FROM equiposref"
    print ("FLAG")
    df = cargador.cargar(consulta=query)
    print (df)
    return dict(zip(df['nombre_equipo'], df['id_equipo']))

def traducir(csv_path, diccionario_equipos):
    df = pd.read_csv(csv_path)
    
    df['id_equipo_local'] = df['HomeTeam'].map(diccionario_equipos)
    df['id_equipo_visitante'] = df['AwayTeam'].map(diccionario_equipos)
    df = df.rename(columns={'Date': 'fecha'})
    
    return df[['fecha', 'id_equipo_local', 'id_equipo_visitante']]


def insertar_calendario(df, cargador):
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True, errors='coerce')
    df['id_equipo_local'] = df['id_equipo_local'].astype('Int64')
    df['id_equipo_visitante'] = df['id_equipo_visitante'].astype('Int64')
    
    cargador.insertar_sin_duplicados(df, 'calendario')

def main():
    script_dir = os.path.dirname(__file__)
    directorio = os.path.join(script_dir, '..', '..', 'datos', 'procesados')
    directorioEntrada = os.path.join(directorio, 'calendario.csv')
    
    cargador = CargadorDatos()
    diccionario = dict_equipos(cargador)
    
    df_traducido = traducir(directorioEntrada, diccionario)
    insertar_calendario(df_traducido, cargador)
    
    cargador.desconectar()


if __name__ == "__main__":
    main()
