import os
import datetime
import subprocess

# Directorio donde está este script
script_dir = os.path.dirname(__file__)

# relativa
directorio = os.path.join(script_dir, '..', '..', 'datos')
directorio_originales = os.path.join(directorio, 'originales')

# Calcular temporada
fecha = datetime.datetime.now()
comienzo = fecha.year % 100
final = (fecha.year + 1) % 100
cadena = f"{comienzo:02d}{final:02d}"

# Liga Premier
division = "E0"
url = f"https://www.football-data.co.uk/mmz4281/{cadena}/{division}.csv"
output_filename = os.path.join(directorio_originales, f"{division}_{cadena}.csv")

# curl para descargar el archivo
subprocess.run(["curl", "-o", output_filename, url])

print(f"Actualizado: {output_filename}")
