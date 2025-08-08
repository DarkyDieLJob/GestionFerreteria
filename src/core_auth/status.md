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

#### Autenticación Vanilla de Django
- ✅ **Configuración Básica**: Correctamente configurada
- 🔄 **Modelo de Usuario**: Usando el modelo por defecto de Django
- 🔍 **URLs de Autenticación**: No definidas aún

#### Autenticación Social (allauth)
- ⚠️ **Configuración Inicial**: Básica configurada, faltan URLs
- 🔑 **Credenciales**: Cargadas desde variables de entorno
- 🌐 **Sitio Configurado**: `SITE_ID = 2`

## Próximos Pasos

1. **Autenticación Vanilla**:
   - Implementar vistas y URLs básicas
   - Crear plantillas para login/registro

2. **Autenticación Social**:
   - Configurar URLs de allauth
   - Verificar credenciales de proveedores
   - Configurar redirecciones

3. **Seguridad**:
   - Mover `SECRET_KEY` a variables de entorno
   - Ajustar `DEBUG` y `ALLOWED_HOSTS` para producción

4. **Pruebas**:
   - Implementar pruebas de autenticación