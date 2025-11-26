import subprocess
import sys
import os
from datetime import datetime
import shutil

script_dir = os.path.dirname(__file__)

# Rutas a los scripts
script_preprocesar = os.path.join(script_dir, '..', 'preprocesador', 'preprocesar.py')
script_entrenamiento = os.path.join(script_dir,'..', 'red',  'entrenamiento.py')
script_procesar = os.path.join(script_dir, '..', 'evaluar', 'procesar.py')

def ejecutar_script(ruta_script):
    print(f"\nEjecutando: {os.path.basename(ruta_script)} a las {datetime.now()}")
    try:
        resultado = subprocess.run(
            [sys.executable, ruta_script],
            check=True,
            capture_output=True,
            text=True,
            timeout=60  
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
    scripts = [script_preprocesar, script_entrenamiento, script_procesar]
    exitosos = 0
    fallidos = 0
    for ruta in scripts:
        if ejecutar_script(ruta):
            exitosos += 1
        else:
            fallidos += 1
    print(f"\nEjecutados exitosamente: {exitosos}, Fallidos: {fallidos}")
    # Finalmente, copiar los archivos generados a la carpeta web
    script_dir = os.path.dirname(__file__)

    ruta_origen = os.path.join(script_dir, '..', '..', 'datos', 'procesados')
    ruta_destino = os.path.join(script_dir, '..', '..', 'web')

    shutil.copy(os.path.join(ruta_origen, 'predicciones.json'), os.path.join(ruta_destino, 'predicciones.json'))
    shutil.copy(os.path.join(ruta_origen, 'partidosBD.json'), os.path.join(ruta_destino, 'partidosBD.json'))

    sys.exit(0 if fallidos == 0 else 1)

if __name__ == "__main__":
    main()
