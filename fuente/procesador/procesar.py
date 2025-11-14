import os
import json
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import torch.nn as nn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# rutas relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_root = os.path.dirname(script_dir)
from conexion.config import COLUMNAS_USAR

from conexion.conexion import CargadorDatos
from conexion.config import  MAPEO_RESULTADO, MAPEO_RESULTADO_INV
from evaluador import EvaluadorModelo
from red.red import RedNeuronal  

class ProcesarDatos:
    def __init__(self):
        #Inicializa el procesador
        #ruta_json_pasados: Ruta al archivo partidosPasados.json
        self.ruta_json_pasados = os.path.join(script_dir, '..', 'datos', 'procesados', 'partidosPasados.json')
            
        self.cargador = CargadorDatos()
        self.df_calendario = None
        self.df_partidos_pasados = None
        self.df_partidos_futuros = None
        
    def recuperar_calendario(self):
        try:
            query = "SELECT * FROM calendario ORDER BY fecha ASC"
            self.df_calendario = self.cargador.cargar(consulta=query) 
            print("Calendario recuperado, total partidos:", len(self.df_calendario))  
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
        print(f"pasados: {len(self.df_partidos_pasados)}")
        print(f"Futuros: {len(self.df_partidos_futuros)}")
        
        return self.df_partidos_pasados, self.df_partidos_futuros
    
    def agregar_predicciones_historicas(self, df_predicciones_modelo):
        # Mapeo de predicciones
        df_procesado = self.df_partidos_pasados.copy()
        
        # Fusionar con predicciones del modelo
        df_procesado = df_procesado.merge(
            df_predicciones_modelo,
            on=['id_equipo_local', 'id_equipo_visitante', 'fecha'],
            how='left'
        )
        
        # Agregar columna de resultado predicho (solo si prediccion_modelo no es nulo)
        df_procesado['resultado_predicho'] = df_procesado.apply(
            lambda row: MAPEO_RESULTADO_INV.get(row.get('prediccion'), None) 
            if pd.notna(row.get('prediccion_modelo')) else None,
            axis=1
        )
        
        # Agregar columna de predicción correcta
        # Comparar resultado_final (guardado en JSON como número) 
        # con resultado_predicho (letra de la BD)
        df_procesado['prediccion_correcta'] = df_procesado.apply(
            lambda row: (
                MAPEO_RESULTADO.get(row['resultado_final']) == 
                row.get('prediccion')
            ) if pd.notna(row.get('prediccion')) else None,
            axis=1
        )
        
        return df_procesado
    
    def actualizar_json_partidos_pasados(self, df_actualizado):

        # Cargar JSON
        datos_json = json.load(self.ruta_json_pasados, 'r', encoding='utf-8')

        # Convertir DataFrame a lista de diccionarios
        nuevos_registros = df_actualizado.to_dict('records')
        
        # Actualizar registros existentes o agregar nuevos
        for nuevo_registro in nuevos_registros:
            encontrado = False
            for i, registro_json in enumerate(datos_json):
                if (registro_json.get('id_equipo_local') == nuevo_registro.get('id_equipo_local') and
                    registro_json.get('id_equipo_visitante') == nuevo_registro.get('id_equipo_visitante') and
                    str(registro_json.get('fecha')) == str(nuevo_registro.get('fecha'))):
                    # Actualizar registro
                    datos_json[i].update({
                        'resultado_predicho': nuevo_registro.get('resultado_predicho'),
                        'prediccion_correcta': nuevo_registro.get('prediccion_correcta')
                    })
                    encontrado = True
                    break
            
            if not encontrado:
                # Agregar nuevo registro
                datos_json.append(nuevo_registro)
        
        # Guardar JSON actualizado
        with open(self.ruta_json_pasados, 'w', encoding='utf-8') as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=2, default=str)
        
        return True
            
    
    def procesar_ciclo_completo(self, df_predicciones_modelo=None):  
       # Paso 1: Recuperar calendario
        self.recuperar_calendario()
        
        # Paso 2: Dividir partidos
        self.dividir_partidos()
        
        # Paso 3: Agregar predicciones=
        if df_predicciones_modelo is not None:
            df_actualizado = self.agregar_predicciones_historicas(df_predicciones_modelo)
            self.actualizar_json_partidos_pasados(df_actualizado)
        
        return self.df_partidos_futuros, self.df_partidos_pasados
    
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
        df_futuros, df_pasados = procesador.procesar_ciclo_completo()
        print(df_futuros)
        # Los partidos futuros se pasarán al evaluador
        evaluador_modelo = EvaluadorModelo()
        evaluador_modelo.procesar_ciclo_completo(df_futuros, modelo)
    finally:
        procesador.desconectar()