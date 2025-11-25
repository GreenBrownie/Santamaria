import os
import json
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import torch.nn as nn
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# rutas relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_root = os.path.dirname(script_dir)
from conexion.config import COLUMNAS_USAR

from conexion.conexion import CargadorDatos
from evaluador import EvaluadorModelo
from red.entrenamiento import RedNeuronal  

class ProcesarDatos:
    def __init__(self):
        #Inicializa el procesador
        self.ruta_json_predicciones = os.path.join(script_dir,'..' ,'..', 'datos', 'procesados', 'partidosBD.json')
            
        self.cargador = CargadorDatos()
        self.df_calendario = None
        self.df_partidos_futuros = None
        
    def recuperar_calendario(self):
        try:
            query = "SELECT * FROM partidosml ORDER BY fecha ASC"
            self.df_calendario = self.cargador.cargar(consulta=query) 
            return self.df_calendario
        except Exception as e:
            print(f"error: {e}")
            return None
    
    def dividir_partidos(self):
        #Divide los partidos en pasados y futuros según la fecha actual REDUNDANCIA
        if self.df_calendario is None:
            self.recuperar_calendario()
        
        fecha_actual = datetime.now().date()
        
        # no se si es necesesario esto
        self.df_calendario['fecha'] = pd.to_datetime(self.df_calendario['fecha'])
        
        self.df_partidos_pasados = self.df_calendario[self.df_calendario['fecha'].dt.date <= fecha_actual].copy()
        
        self.df_partidos_futuros = self.df_calendario[self.df_calendario['fecha'].dt.date > fecha_actual].copy()
        
        print(f"Partidos a la fecha {fecha_actual}: diivididos")
        print(f"Futuros: {len(self.df_partidos_futuros)}")
        
        return self.df_partidos_futuros
        
    def base_a_json(self, orient='records'):
        query = "SELECT * FROM partidosml ORDER BY fecha ASC"
        bdDf=self.cargador.cargar(consulta=query)

        #Fix para la hora
        if 'hora' in bdDf.columns:
                def safe_hora_format(r):
                    if pd.isna(r.hours):
                        return None
                    return f"{int(r.hours):02d}:{int(r.minutes):02d}:{int(r.seconds):02d}"

                td = pd.to_timedelta(bdDf['hora'])
                comps = td.dt.components
                bdDf['hora'] = comps.apply(safe_hora_format, axis=1)

        bdDf = bdDf.applymap(lambda x: x.isoformat() if hasattr(x, "isoformat") else x)

        bdDf = bdDf.where(pd.notna(bdDf), None)
        bdDf = bdDf.replace({np.nan: None, float('inf'): None, -float('inf'): None})
        data = bdDf.to_dict(orient=orient)

        with open(self.ruta_json_predicciones, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)



    def procesar_ciclo_completo(self, df_predicciones_modelo=None):  
       # Paso 1: Recuperar calendario
        self.recuperar_calendario()
        
        # Paso 2: Dividir partidos
        self.dividir_partidos()

        return self.df_partidos_futuros
    
    def desconectar(self):
        self.cargador.desconectar()
        print("Conexión cerrada")

# main
if __name__ == "__main__":
    procesador = ProcesarDatos()
    
    try:
        #recuperar arquitectura del modelo
        modelo = RedNeuronal(len(COLUMNAS_USAR)-1)
        # Obtener partidos futuros y pasados
        df_futuros = procesador.procesar_ciclo_completo()
        print(df_futuros)
        # Los partidos futuros se pasarán al evaluador
        evaluador_modelo = EvaluadorModelo()
        evaluador_modelo.procesar_ciclo_completo(df_futuros, modelo)

        # Guardar JSON de la base de datos completa
        procesador.base_a_json( orient='records')

    finally:
        procesador.desconectar()