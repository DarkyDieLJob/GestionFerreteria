# Estado de la Aplicación Django: core_auth

## Estructura del Proyecto
- Arquitectura limpia (clean architecture) con separación clara entre:
  - `adapters/`: Implementaciones concretas
  - `domain/`: Lógica de negocio
  - `tests/`: Pruebas unitarias

## Configuración de Autenticación

### Configuración Actual
1. **Backends de Autenticación**:
   - `django.contrib.auth.backends.ModelBackend` (estándar de Django)
   - `allauth.account.auth_backends.AuthenticationBackend` (social)

2. **Aplicaciones Instaladas**:
   - `django-allauth` para autenticación social
   - `rest_framework` y `rest_framework.authtoken` para API

3. **Proveedores Sociales**:
   - Google
   - GitHub (con variables de entorno)

### Estado Actual

#### Autenticación Básica de Django
- ✅ **Configuración Básica**: Implementada y operativa
- 🔄 **Modelo de Usuario**: Usando el modelo por defecto de Django
- 🔍 **URLs de Autenticación**: Definidas en `core_config/urls.py` o incluidas desde `core_auth`
- 🧩 **Cambio de contraseña forzado**: Vista usa `EnforcedPasswordChangeForm` con mensaje de error en español para contraseña actual incorrecta (incluye "incorrecta")

#### Autenticación Social (allauth)
- 🔄 **Estado**: Opcional; disponible y documentada, puede activarse por entorno
- 🔑 **Credenciales**: Desde variables de entorno
- 🌐 **Sitio Configurado**: `SITE_ID` configurable

## Próximos Pasos

1. **Autenticación Básica**:
   - Afinar templates y UX donde sea necesario
   - Revisar mensajes e i18n

2. **Autenticación Social**:
   - Habilitar proveedores requeridos según despliegue
   - Verificar redirecciones y permisos

3. **Seguridad**:
   - Mover `SECRET_KEY` a variables de entorno
   - Ajustar `DEBUG` y `ALLOWED_HOSTS` para producción

4. **Pruebas**:
   - ✅ Suite actual pasa al 100%; mantener cobertura y añadir casos nuevos si se habilita social auth