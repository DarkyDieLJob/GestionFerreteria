# Registro de Cambios - Módulo core_auth

Este documento registra los cambios realizados en el módulo de autenticación (`core_auth`).

## [2025-08-07]

### Añadido
- Estructura inicial del proyecto siguiendo arquitectura hexagonal
- Documentación detallada en `core_auth_specifications.md`
- Plantillas base para autenticación:
  - `templates/auth/base.html` - Plantilla base con estilos Tailwind CSS
  - `templates/auth/login.html` - Formulario de inicio de sesión
  - `templates/auth/register.html` - Formulario de registro
  - `templates/auth/logout.html` - Confirmación de cierre de sesión
- Vistas de autenticación en `adapters/views.py`:
  - `RegisterView` - Maneja el registro de nuevos usuarios
    - Valida el formulario de registro
    - Ejecuta el caso de uso `RegisterUserUseCase`
    - Redirige al login tras registro exitoso
  - `LoginView` - Maneja el inicio de sesión
    - Valida credenciales
    - Ejecuta el caso de uso `LoginUserUseCase`
    - Maneja la opción "Recordarme"
    - Redirige al home tras inicio de sesión exitoso
  - `LogoutView` - Maneja el cierre de sesión
    - Ejecuta el caso de uso `LogoutUserUseCase`
    - Redirige al login tras cerrar sesión
- Formularios de autenticación en `adapters/forms.py`:
  - `LoginForm` - Para el inicio de sesión con validación de credenciales
    - Campo `username_or_email` que acepta nombre de usuario o correo
    - Validación personalizada para credenciales incorrectas
    - Estilo con Tailwind CSS
  - `RegisterForm` - Para el registro de nuevos usuarios
    - Campos: `username`, `email`, `password1`, `password2`, `terms`
    - Validación de correo único
    - Validación de contraseña segura (mínimo 8 caracteres)
    - Aceptación de términos y condiciones requerida
    - Internacionalización de mensajes de error
- Interfaz `AuthRepository` en `ports/interfaces.py` con los métodos:
  - `create_user()` - Para crear nuevos usuarios
  - `authenticate_user()` - Para autenticar usuarios
  - `logout_user()` - Para cerrar sesión
- Implementación de `DjangoAuthRepository` en `adapters/repository.py`:
  - `create_user()` - Crea usuarios con validación de unicidad
  - `authenticate_user()` - Soporta autenticación por nombre de usuario o email
  - `logout_user()` - Cierra la sesión del usuario actual

### Añadido
- Configuración de URLs en `adapters/urls.py`:
  - `/auth/login/` - Para la vista de inicio de sesión
  - `/auth/register/` - Para la vista de registro
  - `/auth/logout/` - Para la vista de cierre de sesión
- Inclusión de las URLs de autenticación en `core_config/urls.py` con el namespace 'core_auth'
- Plantilla base mejorada en `templates/auth/base.html`:
  - Diseño limpio y responsivo con Tailwind CSS
  - Bloques para título, contenido, título de tarjeta y enlaces de pie de página
  - Estilos mejorados para mensajes de éxito/error
  - Tipografía Inter mejorada
  - Estructura de tarjeta centrada con sombras sutiles
- Plantilla de inicio de sesión en `templates/auth/login.html`:
  - Formulario de inicio de sesión con validación
  - Campos para usuario/correo y contraseña
  - Opción "Recordar sesión"
  - Enlace a recuperación de contraseña
  - Enlace a la página de registro
  - Mensajes de error integrados
  - Diseño responsivo y accesible
- Plantilla de registro en `templates/auth/register.html`:
  - Formulario de registro con validación
  - Campos para nombre de usuario, correo y contraseña
  - Validación de contraseña segura
  - Términos y condiciones
  - Enlace a la página de inicio de sesión
  - Mensajes de error detallados
  - Diseño consistente con la plantilla base
- Plantilla de cierre de sesión en `templates/auth/logout.html`:
  - Mensaje de confirmación de cierre de sesión
  - Icono de verificación
  - Botón para volver al inicio de sesión
  - Diseño limpio y minimalista
  - Estilos consistentes con el resto de la aplicación

### Implementados
- Casos de uso en `domain/use_cases.py`:
  - `RegisterUserUseCase`: Maneja el registro de nuevos usuarios con validaciones
  - `LoginUserUseCase`: Gestiona la autenticación de usuarios y sesiones
  - `LogoutUserUseCase`: Se encarga del cierre seguro de sesiones
  - Validaciones de negocio y manejo de errores
  - Documentación completa de métodos y clases

- Pruebas unitarias en `tests/test_use_cases.py`:
  - `TestRegisterUserUseCase`: Pruebas para el registro de usuarios exitoso y con errores
  - `TestLoginUserUseCase`: Pruebas para inicio de sesión con diferentes escenarios
  - `TestLogoutUserUseCase`: Pruebas para el cierre de sesión
  - Cobertura de casos de éxito y de error
  - Uso de mocks para aislar las pruebas

### Corregido
- Errores en las pruebas de `TestLoginUserUseCase`:
  - Las pruebas `test_login_success_with_username` y `test_login_success_with_email` fallaban debido a una discrepancia en cómo se llamaba al método `authenticate_user` en los mocks.
  - Se actualizaron las pruebas para que coincidan con la implementación real del método.

### Añadido
- Pruebas exhaustivas para `DjangoAuthRepository` en `tests/test_adapters.py`:
  - Pruebas de creación de usuarios exitosa
  - Manejo de nombres de usuario duplicados
  - Manejo de correos electrónicos duplicados
  - Autenticación exitosa con nombre de usuario y correo electrónico
  - Manejo de credenciales inválidas
  - Pruebas de cierre de sesión

### Cambiado
- Actualizado `ports/interfaces.py` para incluir la nueva interfaz `AuthRepository`
- Mejorada la documentación en varios archivos
- Actualizado `adapters/repository.py` con la nueva implementación

### Pendiente
- Crear vistas para manejar las solicitudes de autenticación
- Configurar las URLs para las vistas de autenticación
- Implementar pruebas unitarias para los casos de uso

---
*Este archivo se actualizará con cada cambio significativo en el módulo.*
