# EmpresaHub

Aplicación web ligera para equipos que necesitan compartir archivos y gestionar tareas de forma colaborativa. Permite que cada colaborador suba fotografías o documentos, consulte los archivos disponibles y registre tareas con responsables y fechas de vencimiento.

## Características

- Panel principal con resumen de tareas activas y últimas cargas.
- Módulo de subida de archivos con campos de descripción y registro automático de usuarios.
- Gestión de tareas con asignación opcional a colaboradores, fecha límite y control de estado.
- Almacenamiento local mediante SQLite y archivos guardados en el directorio `app/uploads/`.

## Requisitos

- Python 3.10 o superior
- Dependencias listadas en `requirements.txt`

## Puesta en marcha

1. Crear y activar un entorno virtual (opcional pero recomendado).
2. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Inicializar y ejecutar la aplicación:

   ```bash
   export FLASK_APP=app.app:create_app
   flask run
   ```

   La aplicación estará disponible en `http://127.0.0.1:5000/`.

## Personalización

- **Límites de tamaño**: se puede ajustar la constante `MAX_CONTENT_LENGTH` en `app/app.py`.
- **Tipos de archivo permitidos**: modificar el conjunto `ALLOWED_EXTENSIONS` para habilitar otros formatos.
- **Persistencia en producción**: considere montar un volumen para `app/uploads/` y configurar `DATABASE_URL` a un motor gestionado.

## Nota de seguridad

Esta demo no incluye autenticación ni control de permisos. Para entornos reales es recomendable integrar un sistema de usuarios con credenciales, conexiones HTTPS y antivirus para los archivos cargados.
