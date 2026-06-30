# Plan de Implementación: Reconocimiento Facial y Despliegue en Cloudflare

Este plan detalla los cambios técnicos solicitados para el proyecto "Pantano de Shrek".

> [!WARNING]
> **Limitación Técnica Importante (OpenCV en Web)**
> El proyecto utiliza `cv2.VideoCapture(0)` (OpenCV) para acceder a la cámara web. Esta es una librería nativa de Python/C++ que accede al hardware del sistema operativo local. 
> Si exportamos la aplicación como un sitio web estático para **Cloudflare Pages** (usando Pyodide/Flet publish), el código de OpenCV **no funcionará** en el navegador de los usuarios porque los navegadores por seguridad no permiten a Python nativo acceder al hardware directamente; requieren APIs de JavaScript (`getUserMedia`). 
> **¿Deseas que documente el despliegue a pesar de esta limitación, o prefieres buscar una alternativa de alojamiento (como un VPS o Render) donde la app de Flet corra en modo servidor?**

## Cambios Propuestos: Reconocimiento Facial

### 1. Sistema de Almacenamiento de Imágenes
- **[NEW] Carpeta `Image/`**: Se creará en la raíz del proyecto (`c:\Users\cariv\Downloads\proyecto_pantano\proyecto_pantano\Image`).
- **[MODIFY] `views/register.py`**: 
  - Al tomar la foto con la cámara, la imagen dejará de guardarse en base64 en memoria (`USERS_DB`).
  - La imagen capturada se guardará físicamente en la carpeta `Image/` con el nombre `<nombre_de_usuario>.png`.
  - El diccionario `USERS_DB` guardará la referencia/ruta a la imagen o simplemente asumiremos que si el usuario existe, su foto es `<usuario>.png`.

### 2. Eliminación de Modo "Místico" (Simulación)
- **[MODIFY] `views/register.py`**: Se eliminarán los SVGs simulados, el botón para cambiar de modo cámara/simulación y toda la lógica de `start_simulation_capture`. El sistema exigirá cámara real.
- **[MODIFY] `views/login.py`**: Se eliminará el modo "simulación", su lógica, animaciones SVG y botones relacionados. 

### 3. Login Inteligente (Sin Combobox)
- **[MODIFY] `views/login.py`**:
  - Se eliminará el menú desplegable (`user_dropdown`) que obligaba al usuario a seleccionarse a sí mismo.
  - La función `build_face_recognizer()` se actualizará para leer todas las imágenes `.png` dentro de la carpeta `Image/`, entrenando el modelo LBPH y mapeando los rostros a los nombres de los archivos.
  - Al abrir el escaner, la cámara detectará el rostro y el modelo predecirá quién es. Si la confianza es alta (coincidencia), el sistema iniciará sesión automáticamente con el usuario detectado.

---

## Documentación: Despliegue en Cloudflare Pages y GitHub

A continuación, los pasos documentados para conectar el repositorio a Cloudflare Pages (asumiendo que se despliega como web estática con Pyodide, teniendo en cuenta la advertencia superior).

### 1. Preparación en GitHub
Asegúrate de que tu repositorio (`https://github.com/cariveraz0/Pantano-de-Shrek`) tenga un archivo `requirements.txt` en la raíz. Debe contener:
```text
flet
opencv-python
numpy
```

### 2. Conexión en Cloudflare Pages
1. Inicia sesión en el [Dashboard de Cloudflare](https://dash.cloudflare.com/).
2. Ve a la sección **Workers & Pages** en el menú izquierdo y haz clic en **Create application** -> Pestaña **Pages** -> **Connect to Git**.
3. Autoriza a Cloudflare a acceder a tu cuenta de GitHub y selecciona el repositorio `Pantano-de-Shrek`.
4. En **Set up builds and deployments**, configura lo siguiente:
   - **Project name**: (Elige un nombre, ej. pantano-shrek)
   - **Production branch**: `main` (o `master`)
   - **Framework preset**: `None`
   - **Build command**: `pip install flet && flet publish main.py`
   - **Build output directory**: `dist`
5. Haz clic en **Save and Deploy**. Cloudflare ejecutará el comando y publicará el sitio.

### 3. Configuración de Dominio Personalizado (HTTPS)
1. Una vez desplegado el proyecto, ve a la pestaña **Custom Domains** dentro de la configuración de tu proyecto en Cloudflare Pages.
2. Haz clic en **Set up a custom domain**.
3. Ingresa tu dominio (ej. `midominio.com`).
4. Cloudflare te pedirá actualizar los registros DNS (usualmente un CNAME apuntando a tu URL temporal de `*.pages.dev`).
5. Al usar Cloudflare, el certificado **SSL/TLS (HTTPS)** se genera y habilita automáticamente en los servidores de borde (Edge).

## Preguntas Abiertas
- Revisa la advertencia sobre OpenCV en el navegador para Cloudflare Pages. ¿Procedemos con los cambios de código locales y dejo la documentación tal como está?
