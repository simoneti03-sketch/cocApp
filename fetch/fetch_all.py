import subprocess
import os
import sys

# Lista actualizada de scripts
scripts = [
    "fetch_defenses.py",      # Defensas (Clave TH)
    "fetch_army.py",          # Cuarteles/Campamentos (Clave TH)
    "fetch_resources_data.py", # Minas/Almacenes (Clave TH)
    "fetch_traps_data.py",     # Trampas (Clave TH)
    "fetch_heroes.py",         # Héroes (Clave HH)
    "fetch_pets_data.py",      # Mascotas (Clave PH)
    "fetch_units.py",          # Tropas Elixir/Oscuras (Clave LL)
    "fetch_spells.py",         # Hechizos Elixir/Oscuros (Clave LL)
    "fetch_siege_data.py"      # Máquinas de Asedio (Clave LL)
]

def run_all():
    # Detectar la carpeta donde está este script maestro (fetch/)
    fetch_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Usar el mismo ejecutable de Python que está corriendo este script (el del venv)
    python_executable = sys.executable
    
    print("=== INICIANDO ACTUALIZACIÓN COMPLETA DE DATA1 ===")
    print(f"Carpeta de trabajo: {fetch_dir}")
    print(f"Python en uso: {python_executable}\n")

    for script in scripts:
        script_path = os.path.join(fetch_dir, script)
        print(f"--- Ejecutando: {script} ---")
        
        try:
            # Ejecutamos con cwd=fetch_dir para que las rutas '..' funcionen bien
            result = subprocess.run(
                [python_executable, script_path], 
                check=True, 
                cwd=fetch_dir
            )
            if result.returncode == 0:
                print(f"✅ {script} completado.\n")
        except subprocess.CalledProcessError:
            print(f"❌ Error crítico en {script}. Continuando con el siguiente...\n")
        except FileNotFoundError:
            print(f"⚠️ No se encontró el archivo: {script}\n")

    print("=== PROCESO FINALIZADO ===")

if __name__ == "__main__":
    run_all()