# 🏰 Clash of Clans Upgrade Tracker

Una herramienta para gestionar el progreso de tus aldeas en Clash of Clans. Calcula tiempos totales de construcción, laboratorio y héroes.

## ✨ Características Principales

- 🚀 **Cálculo Preciso de Tiempos**: Calcula automáticamente cuánto tiempo te queda por cada categoría (Defensas, Héroes, Laboratorio, etc.).
- 🛡️ **Soporte TH17**: Actualizado con los últimos niveles de Ayuntamiento y estructuras.
- 🧪 **Laboratorio y Mascotas**: Seguimiento detallado de tropas, hechizos y mascotas.
- 👷 **Optimización de Constructores**: Detecta automáticamente si tienes el 6º constructor (B.O.B Hut).
- 💾 **Multi-Aldea**: Guarda y gestiona varias cuentas localmente en tu navegador.

## 🛠️ Requisitos del Sistema

Para ejecutar esta aplicación localmente, necesitarás:

- **Python 3.8 o superior**
- **pip** (gestor de paquetes de Python)
- Un navegador (Chrome, Firefox, Edge, Safari)

## 🚀 Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/cocApp.git
cd cocApp
```

### 2. Configurar el entorno virtual (Recomendado)
```bash
python -m venv venv
# En macOS/Linux:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:8080`.

## 📖 Cómo usar la aplicación

1. **Obtener tus datos**: Desde los ajustes del juego darle a exportar datos de aldea json.
2. **Importar**: Haz clic en el botón **"Añadir otra aldea"** y pega el contenido JSON desde tu portapapeles.
3. **Analizar**: La app procesará automáticamente todos tus niveles y te mostrará el progreso comparado con el máximo permitido para tu nivel de Ayuntamiento.
4. **Actualizar**: Cuando subas de nivel en el juego, vuelve a pegar el JSON actualizado y haz clic en **"Actualizar aldea"** para mantener tu progreso al día.

## 🗂️ Estructura del Proyecto

- `app.py`: Servidor Flask y lógica de procesamiento de datos.
- `new_data/`: Base de datos JSON con tiempos, costes y niveles máximos (TH1-TH17).
- `static/`:
    - `script.js`: Lógica del frontend y renderizado dinámico.
    - `style.css`: Estilos.
    - `images/`: Recursos visuales del juego.
- `templates/`: Plantillas HTML (index.html).

---

Las imagenes han sido extraidas de https://clashofclans.fandom.com/wiki/Clash_of_Clans_Wiki


Este proyecto es de código abierto, se agradece cualquier contribución, sugerencia o informe de errores.
Si quieres contribuir, puedes hacer un fork, crear una rama, y luego hacer un pull request.

## CALVO EL QUE LO LEA
