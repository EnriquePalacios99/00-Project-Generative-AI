
# Tutorial de Configuración y Ejecución del Proyecto Alicorp-IAGEN-MVP

Este tutorial describe cómo configurar y ejecutar la aplicación Streamlit que utiliza la API de Gemini y Vertex AI para generar descripciones, imágenes y análisis de feedback de clientes.

## 1. Requisitos previos

- **Python 3.10+**
- **pip** actualizado
- **Cuenta de Google Cloud Platform (GCP)**
- **Proyecto habilitado en GCP** con Vertex AI API activada

## 2. Clonar el repositorio

```bash
git clone https://github.com/usuario/alicorp-iagen-mvp.git
cd alicorp-iagen-mvp
```

## 3. Crear y activar entorno virtual

```bash
python -m venv venv
source venv/bin/activate   # En Linux/Mac
venv\Scripts\activate    # En Windows
```

## 4. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Importante:** Verificar que no existan errores de sintaxis en `requirements.txt` (ejemplo: `google-cloud-aiplatform>=1.70` sin punto final).

## 5. Configurar credenciales en Google Cloud

1. Entra a **IAM & Admin > Service Accounts** en tu consola de Google Cloud.
2. Crea una cuenta de servicio, por ejemplo: `vertexai-service`.
3. Asigna estos roles:
   - Vertex AI User (`roles/aiplatform.user`)
   - Vertex AI Endpoint User (`roles/aiplatform.endpointUser`)
   - Storage Object Viewer (`roles/storage.objectViewer`)
4. Genera y descarga una clave en formato JSON para esta cuenta de servicio.

## 6. Configurar archivo `.env`

En la carpeta raíz del proyecto, crear un archivo `.env` con este contenido:

```env
GOOGLE_API_KEY=TU_API_KEY_DE_GEMINI
GEMINI_MODEL=gemini-2.5-flash-lite
GCP_PROJECT=tu-id-proyecto
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/ruta/completa/tu-clave.json
```

> **Nota:** `GOOGLE_APPLICATION_CREDENTIALS` debe apuntar al archivo JSON descargado en el paso anterior.

## 7. Ejecución de la aplicación

```bash
streamlit run app/01_Descripciones.py
```

También puedes ejecutar otras páginas:

```bash
streamlit run app/pages/02_Imagenes.py
streamlit run app/pages/03_Feedback.py
```

## 8. Funcionalidades principales

### **01_Descripciones**
- Usa la API de Gemini para generar descripciones de productos.

### **02_Imagenes**
- Genera imágenes con fondos promocionales utilizando Vertex AI Imagen.

### **03_Feedback**
- Analiza un archivo CSV con comentarios y realiza un análisis básico de sentimiento.

## 9. Posibles errores y soluciones

- **`PermissionDenied` en Vertex AI:** Revisa que tu cuenta de servicio tenga los roles correctos y que el proyecto y ubicación (`GCP_PROJECT`, `GCP_LOCATION`) estén bien configurados.
- **`GoogleAuthError`:** Verifica que la ruta de `GOOGLE_APPLICATION_CREDENTIALS` sea correcta y que el JSON exista.

## 10. Créditos
Proyecto interno — MVP de generación de contenido con IA.
