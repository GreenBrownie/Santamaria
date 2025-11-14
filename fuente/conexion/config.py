#Configuración de la bd
CONFIG_BD = {
    'host': 'localhost',
    'user': 'root',
    'password': '5514',
    'database': 'partidosBD',
    'port': 3306
}

#Columnas
COLUMNAS_USAR = [
    'fecha',
    'id_equipo_local','id_equipo_visitante',
    'resultado_final',
    'goles_local_ht','goles_visitante_ht',
    'disparos_local','disparos_visitante',
    'disparos_porteria_local','disparos_porteria_visitante',
    'corners_local','corners_visitante',
    'faltas_local', 'faltas_visitante',
    'amarillas_local', 'amarillas_visitante',
    'rojas_local', 'rojas_visitante'
]

# Columnas numéricas
COLUMNAS_NUMERICAS = [
    'fecha',
    #'goles_local_final',
    #'goles_visitante_final',
    'goles_local_ht',
    'goles_visitante_ht','disparos_local',
    'disparos_visitante','disparos_porteria_local','disparos_porteria_visitante',
    'corners_local','corners_visitante',
    'faltas_local','faltas_visitante', 'amarillas_local',
    'amarillas_visitante','rojas_local','rojas_visitante'
]


#Mapeo de resultados
MAPEO_RESULTADO = {
    'A': 0,  # Visitante gana
    'D': 1,  # Empate
    'H': 2   # Local gana
}

MAPEO_RESULTADO_INV = {
    0: 'A',  # Visitante gana
    1: 'D',  # Empate
    2: 'H'   # Local gana
}

#Columnas objetivo (no escalar)
COLUMNAS_OBJETIVO = ['resultado_final', 'goles_local_final', 'goles_visitante_final']
