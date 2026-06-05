# Integración de Amazon S3 en Django

Esta guía detalla el paso a paso para configurar un entorno de almacenamiento en la nube utilizando Amazon S3 para servir archivos estáticos y multimedia (media) en una aplicación de Django, aplicando las mejores prácticas de seguridad y gestión de dependencias.

---

## Fase 1: Creación y Configuración del Bucket S3

1. Ingresa a la consola de AWS y dirígete al servicio **S3**.

2. Haz clic en **Crear bucket** y aplica la siguiente configuración:

   - **Región de AWS:** Selecciona `us-east-1` (Norte de Virginia).

   - **Tipo de bucket:** Uso general *(General purpose)*.
     > El uso general es el estándar recomendado para aplicaciones web. Almacena archivos estáticos e imágenes distribuyéndolos en múltiples zonas de disponibilidad para evitar pérdidas. La opción "Directorio" (S3 Express One Zone) está diseñada para computación de alto rendimiento y latencia ultrabaja en una sola zona, lo cual es innecesario y más costoso para una web convencional.

   - **Espacio de nombres del bucket:** Regional de la cuenta *(Account regional)*.
     > El espacio "Global" requiere que el nombre sea único en todo el mundo. El espacio "Regional" añade tu ID de cuenta y región como sufijo, garantizando unicidad sin riesgo de colisiones. Asegúrate de copiar el nombre completo resultante para tu `.env`.

   - **Propiedad de objetos:** ACL deshabilitadas *(recomendado)*.
     > Históricamente, AWS usaba Listas de Control de Acceso (ACL) para definir permisos archivo por archivo. La práctica moderna y más segura es deshabilitar las ACL y controlar todo el acceso a nivel de bucket mediante políticas centralizadas y URLs prefirmadas.

   - **Configuración de bloqueo de acceso público:** Activar *(Bloquear todo el acceso público)*.
     > Mantendremos el bucket completamente privado. Django se encargará de generar "URLs prefirmadas" temporales cada vez que un usuario necesite acceder a un archivo, protegiendo los recursos contra accesos directos no autorizados.

   - **Cifrado predeterminado:** SSE-S3 *(Claves administradas por Amazon S3)*.

   - **Clave de bucket:** Habilitar.

3. Haz clic en **Crear bucket**.

---

## Fase 2: Configuración de Credenciales (IAM)
> ⚠️ **AVISO PARA USUARIOS DE AWS ACADEMY / LEARNER LABS:**
> Si estás ejecutando este proyecto dentro de un entorno de AWS Academy, la creación de usuarios IAM está restringida. Salta directamente a la sección [Credenciales en AWS Academy](#paso-x-obtención-de-credenciales-en-aws-academy).

### Ruta Estándar (Cuentas propias de AWS)

Si tienes control total sobre tu cuenta de AWS, debes crear un usuario con el principio de menor privilegio.

1. En la consola de AWS, dirígete a **IAM > Usuarios > Crear usuario**.
2. Asigna un nombre (ej: `AWS-S3-USER`) y haz clic en **Siguiente**.
3. En **Opciones de permisos**, selecciona **Adjuntar políticas directamente**.
4. Haz clic en **Crear política** y selecciona la pestaña **JSON**.
5. Pega la siguiente política (reemplazando `mi-app-django-bucket` por el nombre de tu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mi-app-django-bucket",
                "arn:aws:s3:::mi-app-django-bucket/*"
            ]
        }
    ]
}
```

6. Continúa, nombra la política (ej: `AWS-S3-PUBLIC-PERMS`) y créala.
7. Vuelve a la creación del usuario, adjunta esta política recién creada y finaliza.
8. Genera y copia las credenciales: `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`.

---

### Obtención de Credenciales en AWS Academy

En AWS Academy no tenemos permisos para crear usuarios IAM. Usaremos las **credenciales temporales de la sesión**.

1. Al iniciar el laboratorio, haz clic en el botón **AWS Details**.
2. En la sección **AWS CLI**, haz clic en **Show**.
3. Copia las tres variables proporcionadas.

> **Nota importante:** A diferencia de las cuentas estándar, en Academy es obligatorio incluir el `AWS_SESSION_TOKEN`, ya que el laboratorio expira (aproximadamente cada 3 horas) y sin este token AWS rechazará la conexión.

---

## Fase 3: Configuración en Django

### 1. Variables de Entorno (`.env`)

En la raíz de tu proyecto, crea o actualiza tu archivo `.env` con las credenciales obtenidas:

```ini
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=8UdXkbsDT/nbi...
AWS_SESSION_TOKEN=IQoJb3...   # Solo requerido si usas AWS Academy
AWS_STORAGE_BUCKET_NAME=s3-demo-bucket-834220514942-us-east-1-an
AWS_S3_REGION_NAME=us-east-1
```

### 2. Configuración en `settings.py`

Asegúrate de tener instaladas las librerías `django-storages` y `boto3`. Luego actualiza tu `settings.py`:

```python
import os

# 1. Carga de credenciales desde el entorno
AWS_ACCESS_KEY_ID        = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SESSION_TOKEN        = os.getenv('AWS_SESSION_TOKEN')  # Obligatorio para Academy
AWS_SECRET_ACCESS_KEY    = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME  = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME       = os.getenv('AWS_S3_REGION_NAME')

# 2. Configuración de firmas y protocolos
# Requerido por AWS para regiones modernas; asegura peticiones firmadas con el algoritmo más seguro.
AWS_S3_SIGNATURE_VERSION = 's3v4'

# Evita que django-storages intente enviar etiquetas ACL por cada archivo
# (fallaría porque deshabilitamos las ACL en el bucket).
AWS_DEFAULT_ACL = None

# Define cuánto tiempo el navegador debe guardar en caché los archivos descargados de S3.
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# 3. Mapeo de Almacenamiento (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "media",       # Carpeta en S3 para imágenes y archivos subidos.
            "querystring_auth": True,  # Genera URLs prefirmadas (vital para buckets privados).
            "region_name": AWS_S3_REGION_NAME,
        },
    },
    # 'staticfiles' maneja el CSS/JS/Admin -> Se queda en tu servidor local
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

---

## Fase 4: Preparación del Directorio Media

Para que Django pueda mapear y listar correctamente los archivos multimedia a través del `default_storage`:

1. En la consola de S3, ingresa a tu bucket.
2. Haz clic en **Crear carpeta**.
3. Nómbrala exactamente **`media`** y guárdala.
4. Ingresa a esa carpeta y sube manualmente las imágenes que deseas visualizar en la web.

> Al utilizar `location: "media"` en `settings.py`, Django buscará exclusivamente dentro de esta carpeta para listar e interactuar con los archivos en tus vistas.