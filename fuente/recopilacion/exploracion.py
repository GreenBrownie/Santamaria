import pandas as pd
import os

#Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..', '..', 'datos', 'originales')

#Directorio de entrada
directorioEntrada = os.path.join(directorio, 'calendario.csv')

df = pd.read_csv(directorioEntrada, encoding='windows-1252')

#set de nombres de equipos, asumimos que se juega de visita y local por eso basta con una columna
equipos = set(df['HomeTeam'])

with open( os.path.join(directorio, 'equiposCalendario.txt'), 'w', encoding='utf-8') as f:
    for equipo in sorted(equipos):
        f.write(f"{equipo}\n")