import subprocess
import sys
import os
from datetime import datetime

script_dir = os.path.dirname(__file__)

script_curl = os.path.join(script_dir, '..', 'cargar', 'curl.py')
script_extraccion = os.path.join(script_dir, '..', 'cargar', 'extraccion.py')
script_insertar = os.path.join(script_dir, '..', 'cargar', 'insertar.py')

def ejecutar_script(ruta_script):
    print(f"\nEjecutando: {os.path.basename(ruta_script)} a las {datetime.now()}")
    try:
        resultado = subprocess.run(
            [sys.executable, ruta_script],
            check=True,
            capture_output=True,
            text=True,
            timeout=30  
        )
        if resultado.stdout:
            print(f"[STDOUT] {resultado.stdout}")
        if resultado.stderr:
            print(f"[STDERR] {resultado.stderr}")
        print(f"Finalizado: {os.path.basename(ruta_script)} a las {datetime.now()}")
        return True
    except subprocess.TimeoutExpired:
        print(f"Timeout en {os.path.basename(ruta_script)}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {os.path.basename(ruta_script)}")
        print(e.stderr)
        return False
    except Exception as ex:
        print(f"Error inesperado en {os.path.basename(ruta_script)}: {ex}")
        return False

def main():
    scripts = [script_curl, script_extraccion, script_insertar]
    exitosos = 0
    fallidos = 0
    for ruta in scripts:
        if ejecutar_script(ruta):
            exitosos += 1
        else:
            fallidos += 1
    print(f"\nEjecutados bien: {exitosos}, mal: {fallidos}")
    sys.exit(0 if fallidos == 0 else 1)

if __name__ == "__main__":
    main()
