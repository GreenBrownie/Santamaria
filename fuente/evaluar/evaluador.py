import os
import sys
import pandas as pd
import torch
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import text

# Configurar rutas relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_root = os.path.dirname(script_dir)

# rutas relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
proyecto_root = os.path.dirname(script_dir)
from conexion.config import MAPEO_RESULTADO_INV
from conexion.conexion import CargadorDatos

class EvaluadorModelo:
    
    def __init__(self):
        self.cargador = CargadorDatos()
        self.ruta_modelo = os.path.join(script_dir, '..', '..', 'datos', 'procesados', 'modelo.pth')
        self.ruta_json_predicciones = os.path.join(script_dir, '..', '..', 'datos', 'procesados', 'predicciones.json')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def cargar_modelo(self, arquitectura_modelo):
        # Asignar modelo
        self.modelo = arquitectura_modelo
        
        # Cargar del modelo guardado
        self.modelo.load_state_dict(torch.load(self.ruta_modelo, map_location=self.device))
        
        # Mover modelo al dispositivo y modo evaluación
        self.modelo.to(self.device)
        self.modelo.eval()
        
    
    def preparar_entrada_prediccion(self, id_local=None, id_visitante=None):
        # Entrada estandar
        entrada = {
            "fecha": 0.5,
            "id_equipo_local": id_local,
            "id_equipo_visitante": id_visitante,
            "goles_local_ht": 0.5,
            "goles_visitante_ht": 0.5,
            "disparos_local": 0.5,
            "disparos_visitante": 0.5,
            "disparos_porteria_local": 0.5,
            "disparos_porteria_visitante": 0.5,
            "corners_local": 0.5,
            "corners_visitante": 0.5,
            "faltas_local": 0.5,
            "faltas_visitante": 0.5,
            "amarillas_local": 0.5,
            "amarillas_visitante": 0.5,
            "rojas_local": 0.0,
            "rojas_visitante": 0.0
        }
        return entrada
    
    def evaluar_partidos(self, df_partidos_futuros):
        
        predicciones = []
        
        for idx, row in df_partidos_futuros.iterrows():
            try:
                id_local = int(row['id_equipo_local'])
                id_visitante = int(row['id_equipo_visitante'])
                fecha = row['fecha']
                
                # Preparar entrada siguiendo el patrón exacto
                entrada = self.preparar_entrada_prediccion(id_local, id_visitante)
                
                # DataFrame con la entrada
                df = pd.DataFrame([entrada])
                
                # Convertir a tensor
                X = torch.tensor(df.values, dtype=torch.float32).to(self.device)
                
                # Realizar predicción sin calcular gradientes
                with torch.no_grad():
                    salida = self.modelo(X)
                    probs = torch.softmax(salida, dim=1).cpu().numpy()[0]
                
                # Obtener clase predicha (argmax)
                clase_predicha = np.argmax(probs)
                prediccion_letra = MAPEO_RESULTADO_INV[int(clase_predicha)]
                
                # Guardar resultados
                prediccion_dict = {
                    'id_equipo_local': id_local,
                    'id_equipo_visitante': id_visitante,
                    'fecha': pd.Timestamp(fecha),
                    'prediccion': int(clase_predicha),
                    'prediccion_letra': prediccion_letra,
                    'porcentaje_away': float(probs[0] * 100),
                    'porcentaje_draw': float(probs[1] * 100),
                    'porcentaje_home': float(probs[2] * 100)
                }
                
                predicciones.append(prediccion_dict)
                
            except Exception as e:
                print(f"FLAG {idx+1} ({id_local} vs {id_visitante}): {e}\n")
                continue
        
        df_predicciones = pd.DataFrame(predicciones)
        
        return df_predicciones
    
    def guardar_predicciones_json(self, df_predicciones):
        # Recuperar nombres de equipos
        query_equipos = "SELECT id_equipo, nombre_equipo FROM equiposref"
        df_equipos = self.cargador.cargar(consulta=query_equipos)
        #Traducir Id a nombre de equipo.
        dic_equipos = dict(zip(df_equipos['id_equipo'], df_equipos['nombre_equipo']))

        try:
            # Convertir DataFrame a lista de diccionarios
            predicciones_lista = []
            
            for idx, row in df_predicciones.iterrows():
                prediccion_dict = {
                    'id_equipo_local': int(row['id_equipo_local']),
                    'id_equipo_visitante': int(row['id_equipo_visitante']),
                    'nombre_equipo_local': dic_equipos.get(int(row['id_equipo_local']), 'Desconocido'),
                    'nombre_equipo_visitante': dic_equipos.get(int(row['id_equipo_visitante']), 'Desconocido'),
                    'fecha': str(pd.Timestamp(row['fecha']).date()),
                    'prediccion': int(row['prediccion']),
                    'prediccion_letra': row['prediccion_letra'],
                    'porcentaje_away': round(float(row['porcentaje_away']), 2),
                    'porcentaje_draw': round(float(row['porcentaje_draw']), 2),
                    'porcentaje_home': round(float(row['porcentaje_home']), 2),
                    'timestamp_prediccion': datetime.now().isoformat()
                }
                predicciones_lista.append(prediccion_dict)
            
            # Guardar en JSON
            with open(self.ruta_json_predicciones, 'w', encoding='utf-8') as f:
                json.dump(predicciones_lista, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"FLAG {e}")
            return False
    #Query para actualizar la bd con las predicciones 
    def actualizar_predicciones_bd(self, df_predicciones: pd.DataFrame) -> bool:
        actualizado = 0
        errores = 0

        with self.cargador.engine.begin() as operacion:
            for _, row in df_predicciones.iterrows():
                try:
                    fecha = pd.Timestamp(row['fecha']).strftime('%Y-%m-%d')
                    prediccion = row['prediccion_letra']
                    id_local = int(row['id_equipo_local'])
                    id_visitante = int(row['id_equipo_visitante'])

                    query = text("""
                        UPDATE partidosml
                        SET resultado_prediccion = :prediccion
                        WHERE DATE(fecha) = :fecha
                        AND id_equipo_local = :id_local
                        AND id_equipo_visitante = :id_visitante
                    """)

                    result = operacion.execute(query, {
                        "prediccion": prediccion,
                        "fecha": fecha,
                        "id_local": id_local,
                        "id_visitante": id_visitante
                    })

                    if result.rowcount > 0:
                        actualizado += 1
                        print(f"Actualizado: {id_local} vs {id_visitante} ({fecha})  {prediccion}")
                    else:
                        print(f"No encontrado: {id_local} vs {id_visitante} ({fecha})")

                except Exception as e:
                    errores += 1
                    print(f"Error en fila: {e}")
                    continue

        print(f"{actualizado} registros actualizados, {errores} errores.")
        return True
    
    def procesar_ciclo_completo(self, df_partidos_futuros, arquitectura_modelo):
        
        # Paso 1: Cargar modelo
        # Paso 2: Evaluar partidos
        # Paso 3: Guardar en JSON
        self.cargar_modelo(arquitectura_modelo)

        df_predicciones = self.evaluar_partidos(df_partidos_futuros)
        
        if df_predicciones is not None and len(df_predicciones) > 0:
            
            self.guardar_predicciones_json(df_predicciones)
            
            # Paso 4: Actualizar BD
            self.actualizar_predicciones_bd(df_predicciones)
        else:
            print("errror: No se generaron predicciones.")

        
        return df_predicciones
    
    def desconectar(self):
        self.cargador.desconectar()
        print("Conexión cerrada")