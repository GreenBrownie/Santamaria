import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import os
from datetime import time
from sklearn.preprocessing import MinMaxScaler
from conexion.conexion import CargadorDatos
from conexion.config import COLUMNAS_NUMERICAS, MAPEO_RESULTADO, COLUMNAS_USAR

class PreprorocesarDatos:
    #Realiza limpieza, promedios para rellenar nulos, transformación y normalización de datos.
    def __init__(self):
        self.cargador = CargadorDatos()
        self.df_procesado = None
        self.scaler = MinMaxScaler()
    
    def cargar_datos(self) -> pd.DataFrame:

        df = self.cargador.cargar_todos()
        
        columnas_disponibles = [col for col in COLUMNAS_USAR if col in df.columns]
        df = df[columnas_disponibles]
        return df
    
    def convertir_fecha_a_dias(self, df: pd.DataFrame) -> pd.DataFrame:
        # hoy
        hoy = pd.Timestamp.now().normalize()  # 2025-10-24
        
        # diferencia en días
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['dias_desde_fecha'] = (hoy - df['fecha']).dt.days
        # Eliminar la columna fecha original
        df['fecha'] = df['dias_desde_fecha']
        df.drop(columns=['dias_desde_fecha'], inplace=True)
        return df

    def mapear_resultado(self, df: pd.DataFrame) -> pd.DataFrame:
        #Mapea los valores de la columna del resultado según MAPEO_RESULTADO
        df_copy = df.copy()
        df_copy['resultado_final'] = df_copy['resultado_final'].map(MAPEO_RESULTADO)
       # df_copy['resultado_ht'] = df_copy['resultado_ht'].map(MAPEO_RESULTADO)
        return df_copy

    def manejo_nulos(self, df: pd.DataFrame) -> pd.DataFrame:

        #Columnas numéricas: con el promedio de la columna
    #Columna hora: con '20:00:00'
        df_copy = df.copy()
        
        # Susituir valores nulos on el promedio
        for col in COLUMNAS_NUMERICAS:
            if col in df_copy.columns:
                if df_copy[col].isnull().any():
                    promedio = df_copy[col].mean()
                    df_copy[col].fillna(promedio, inplace=True)
        
        # Susituir valores nulos de hora con 20:00:00
        if 'hora' in df_copy.columns:
            if df_copy['hora'].isnull().any():
                nulos_hora = df_copy['hora'].isnull().sum()
                df_copy['hora'].fillna('20:00:00', inplace=True)


        #Pir simplicidad el resultado HT nulo será como el resultado final
        if 'resultado_ht' in df_copy.columns:
            if df_copy['resultado_ht'].isnull().any():
                df_copy['resultado_ht'] = df_copy['resultado_ht'].fillna(df_copy['resultado_final']).astype(int)

        return df_copy
    
    
    def estandarizar_minmax(self, df: pd.DataFrame) -> pd.DataFrame:
        #Estandarizar minmax (0-1)
        df_copy = df.copy()
        
        #columnas numéricas 
        columnas_a_escalar = [col for col in COLUMNAS_NUMERICAS if col in df_copy.columns]
        df_copy[columnas_a_escalar] = self.scaler.fit_transform(df_copy[columnas_a_escalar])
            
        return df_copy
    
    
    
    def procesar(self) -> pd.DataFrame:
        """
        Procesamiento:
        1.Cargar datos
        2. Convertir fecha a días
        3.Mapear resultado_final
        4.Susituir valores nulos
        5.Estandarizar columnas numéricas con MinMax
        """
        print("INICIANDO PROCESAMIENTO DE DATOS")
        
        df = self.cargar_datos()
        df = self.convertir_fecha_a_dias(df)
        df = self.mapear_resultado(df)
        df = self.manejo_nulos(df)
        df = self.estandarizar_minmax(df)
        
        self.df_procesado = df
        print("PROCESAMIENTO COMPLETADO")
        return df
    
    def guardar_json(self, orient: str = 'records') -> str:
        #Directorio donde está este script
        script_dir = os.path.dirname(__file__)
        # relativa
        directorio = os.path.join(script_dir, '..', '..', 'datos')
        
        #Directorio de salida
        directorioSalida = os.path.join(directorio, 'procesados', 'partidosPasados.json')

        # Guardar el DataFrame como JSON
        self.df_procesado.to_json(directorioSalida, orient=orient, date_format='iso', indent=2)
        print(f"JSON completo")
        return directorioSalida
    
    def desconectar(self):
        self.cargador.desconectar()
        print("Conexión cerrada")


# Ejecuta todo
def main():
    procesador = PreprorocesarDatos()
    
    try:
        #Procesar todos los datos
        df_procesado = procesador.procesar()
        
        #Guardar JSON
        procesador.guardar_json( orient='records')
        
    except Exception as e:
        print({str(e)})
    
    finally:
        # Cerrar conexión
        procesador.desconectar()


if __name__ == "__main__":
    main()