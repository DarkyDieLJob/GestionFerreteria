# Especificaciones para la Aplicación `core_auth`

Este documento detalla las especificaciones funcionales y técnicas para implementar la autenticación básica (usuario y contraseña) en la aplicación `core_auth` del proyecto Django base, siguiendo una **arquitectura hexagonal** para garantizar modularidad, testabilidad y separación de preocupaciones. La implementación incluirá URLs, vistas, plantillas HTML con Tailwind CSS, puertos y adaptadores, integrándose con el modelo de usuario por defecto de Django y cumpliendo con los estándares definidos en el proyecto.

## Requisitos Funcionales

1. **Autenticación Básica**:
   - Los usuarios podrán registrarse proporcionando un nombre de usuario, correo electrónico y contraseña.
   - Los usuarios podrán iniciar sesión con su nombre de usuario o correo electrónico y contraseña.
   - Los usuarios podrán cerrar sesión.
   - Se mostrará un formulario de registro con validaciones (contraseña mínima de 8 caracteres, correo electrónico único).
   - Se mostrará un formulario de inicio de sesión con manejo de errores (credenciales inválidas).
   - Redirecciones:
     - Tras registro exitoso, redirigir a la página de inicio de sesión.
     - Tras inicio de sesión exitoso, redirigir a la página principal del proyecto (`core_app` o una página de bienvenida).
     - Tras cerrar sesión, redirigir a la página de inicio de sesión.

2. **Interfaz de Usuario**:
   - Las plantillas HTML (`login.html`, `register.html`, `logout.html`) usarán Tailwind CSS para un diseño moderno y responsivo.
   - Los formularios incluirán mensajes de error claros y estilos consistentes con el proyecto.
   - Se usará una plantilla base (`base.html`) para mantener un diseño uniforme.

3. **Arquitectura Hexagonal**:
   - **Dominio**: Casos de uso para registro, inicio de sesión y cierre de sesión, encapsulando la lógica de negocio.
   - **Puertos**: Interfaces que definan los contratos para interactuar con el sistema de autenticación de Django.
   - **Adaptadores**: Implementaciones específicas para vistas, formularios y modelos de Django.

4. **Seguridad**:
   - Las contraseñas se almacenarán de forma segura usando el sistema de hashing de Django.
   - Las configuraciones sensibles (como `SECRET_KEY`) se cargarán desde el archivo `.env`.
   - El modo `DEBUG` y `ALLOWED_HOSTS` se ajustarán para entornos de producción.

5. **Pruebas**:
   - Pruebas unitarias para casos de uso (en `core_auth/tests/test_use_cases.py`).
   - Pruebas para adaptadores (en `core_auth/tests/test_adapters.py`).
   - Cobertura mínima del 80% usando `pytest-cov`.

## Requisitos Técnicos

- **Backend**:
  - Python 3.8+.
  - Django 4.0.6+.
  - Backend de autenticación: `django.contrib.auth.backends.ModelBackend`.
  - Modelo de usuario: Modelo por defecto de Django (`django.contrib.auth.models.User`).
  - Dependencias: `django` (ya incluido en `requirements/lista_v3.txt`).

- **Frontend**:
  - Tailwind CSS para estilos, integrado en el directorio `frontend/` del proyecto.
  - Plantillas HTML ubicadas en `src/core_auth/templates/auth/`.
  - Sin archivos `.css` externos; los estilos se aplicarán directamente con clases de Tailwind en las plantillas HTML.

- **Base de Datos**:
  - Usar la base de datos por defecto (`default`) definida en `core_config/settings.py`:
    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'data/db_default.sqlite3',
        }
    }
    ```
  - No se requiere una base de datos específica para `core_auth`, ya que usará el modelo de usuario de Django.

## Diseño y Arquitectura

### Estructura de la Aplicación `core_auth`
La aplicación seguirá la arquitectura hexagonal con la siguiente estructura:

```
src/core_auth/
├── __init__.py
├── adapters/
│   ├── __init__.py
│   ├── forms.py         # Formularios de Django para registro e inicio de sesión
│   ├── repository.py    # Adaptador para interactuar con el modelo de usuario
│   ├── urls.py          # URLs específicas de autenticación
│   ├── views.py         # Vistas para manejar las solicitudes HTTP
├── domain/
│   ├── __init__.py
│   ├── use_cases.py     # Casos de uso para autenticación
├── ports/
│   ├── __init__.py
│   ├── interfaces.py    # Interfaces para el repositorio de autenticación
├── templates/
│   ├── auth/
│   │   ├── base.html    # Plantilla base con Tailwind CSS
│   │   ├── login.html   # Formulario de inicio de sesión
│   │   ├── register.html # Formulario de registro
│   │   ├── logout.html  # Página de confirmación de cierre de sesión
├── tests/
│   ├── __init__.py
│   ├── test_use_cases.py # Pruebas para casos de uso
│   ├── test_adapters.py  # Pruebas para adaptadores
├── admin.py             # Configuración del panel de administración
├── apps.py              # Configuración de la aplicación
└── migrations/
    ├── __init__.py
```

### Componentes Principales

1. **Dominio (`domain/use_cases.py`)**:
   - **Casos de Uso**:
     - `RegisterUserUseCase`: Registra un nuevo usuario con nombre de usuario, correo electrónico y contraseña.
     - `LoginUserUseCase`: Autentica a un usuario con nombre de usuario/correo electrónico y contraseña.
     - `LogoutUserUseCase`: Cierra la sesión de un usuario.
   - Cada caso de uso interactúa con el repositorio a través de una interfaz definida en `ports/interfaces.py`.

2. **Puertos (`ports/interfaces.py`)**:
   - **Interfaz `AuthRepository`**:
     - Método `create_user`: Crea un usuario con los datos proporcionados.
     - Método `authenticate_user`: Autentica a un usuario con credenciales.
     - Método `logout_user`: Cierra la sesión de un usuario.

3. **Adaptadores**:
   - **`adapters/repository.py`**: Implementa la interfaz `AuthRepository` usando el modelo `User` de Django.
   - **`adapters/forms.py`**: Define formularios para registro (`RegisterForm`) e inicio de sesión (`LoginForm`).
   - **`adapters/views.py`**: Vistas de Django para manejar solicitudes HTTP (registro, inicio de sesión, cierre de sesión).
   - **`adapters/urls.py`**: Define las URLs para las vistas de autenticación.

4. **Plantillas (`templates/auth/`)**:
   - **`base.html`**: Plantilla base con Tailwind CSS, incluyendo un `{% block content %}` para contenido específico.
   - **`login.html`**: Formulario de inicio de sesión con campos para nombre de usuario/correo electrónico y contraseña, estilizado con Tailwind.
   - **`register.html`**: Formulario de registro con campos para nombre de usuario, correo electrónico y contraseña, estilizado con Tailwind.
   - **`logout.html`**: Página de confirmación de cierre de sesión con un botón para volver a la página de inicio de sesión.

5. **Pruebas**:
   - **`tests/test_use_cases.py`**: Pruebas unitarias para los casos de uso, simulando el repositorio con mocks.
   - **`tests/test_adapters.py`**: Pruebas para los adaptadores, incluyendo formularios, vistas y el repositorio.

## Instrucciones para la Implementación

### 1. Configurar la Aplicación `core_auth`
- Asegúrate de que `core_auth` esté en `INSTALLED_APPS` en `core_config/settings.py`:
  ```python
  INSTALLED_APPS = [
      ...
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'core_auth',
      ...
  ]
  ```
- Configura el backend de autenticación en `core_config/settings.py`:
  ```python
  AUTHENTICATION_BACKENDS = [
      'django.contrib.auth.backends.ModelBackend',
  ]
  ```
- Asegúrate de que las variables de entorno estén configuradas en `.env`:
  ```
  SECRET_KEY=tu_clave_secreta
  DEBUG=True
  ```
- Verifica que la base de datos por defecto esté configurada en `core_config/settings.py`:
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'data/db_default.sqlite3',
      }
  }
  ```

### 2. Crear URLs (`adapters/urls.py`)
- Define las URLs para las vistas de autenticación:
  - `/auth/login/`: Para el formulario de inicio de sesión.
  - `/auth/register/`: Para el formulario de registro.
  - `/auth/logout/`: Para cerrar sesión.
- Estructura sugerida:
  ```python
  from django.urls import path
  from . import views

  app_name = 'core_auth'
  urlpatterns = [
      path('login/', views.LoginView.as_view(), name='login'),
      path('register/', views.RegisterView.as_view(), name='register'),
      path('logout/', views.LogoutView.as_view(), name='logout'),
  ]
  ```
- Incluir las URLs en `core_config/urls.py`:
  ```python
  from django.urls import path, include

  urlpatterns = [
      ...
      path('auth/', include('core_auth.adapters.urls', namespace='core_auth')),
      ...
  ]
  ```

### 3. Crear Puertos (`ports/interfaces.py`)
- Define la interfaz `AuthRepository` con los métodos necesarios para interactuar con el sistema de autenticación:
  ```python
  from abc import ABC, abstractmethod
  from django.contrib.auth.models import User

  class AuthRepository(ABC):
      @abstractmethod
      def create_user(self, username: str, email: str, password: str) -> User:
          pass

      @abstractmethod
      def authenticate_user(self, username: str, password: str) -> User:
          pass

      @abstractmethod
      def logout_user(self, request) -> None:
          pass
  ```

### 4. Crear Casos de Uso (`domain/use_cases.py`)
- Implementa los casos de uso para manejar la lógica de negocio:
  - `RegisterUserUseCase`: Valida los datos y crea un usuario.
  - `LoginUserUseCase`: Autentica al usuario y maneja errores.
  - `LogoutUserUseCase`: Cierra la sesión.
- Estructura sugerida:
  ```python
  from django.contrib.auth import login, logout
  from .ports.interfaces import AuthRepository
  from django.core.exceptions import ValidationError

  class RegisterUserUseCase:
      def __init__(self, auth_repository: AuthRepository):
          self.auth_repository = auth_repository

      def execute(self, username: str, email: str, password: str) -> bool:
          try:
              self.auth_repository.create_user(username, email, password)
              return True
          except ValidationError:
              return False

  class LoginUserUseCase:
      def __init__(self, auth_repository: AuthRepository):
          self.auth_repository = auth_repository

      def execute(self, request, username: str, password: str) -> bool:
          user = self.auth_repository.authenticate_user(username, password)
          if user:
              login(request, user)
              return True
          return False

  class LogoutUserUseCase:
      def __init__(self, auth_repository: AuthRepository):
          self.auth_repository = auth_repository

      def execute(self, request) -> None:
          self.auth_repository.logout_user(request)
  ```

### 5. Crear Adaptadores
- **Repositorio (`adapters/repository.py`)**:
  - Implementa la interfaz `AuthRepository` usando el modelo `User` de Django.
  - Ejemplo:
    ```python
    from django.contrib.auth.models import User
    from django.contrib.auth import authenticate, logout
    from django.core.exceptions import ValidationError
    from ..ports.interfaces import AuthRepository

    class DjangoAuthRepository(AuthRepository):
        def create_user(self, username: str, email: str, password: str) -> User:
            if User.objects.filter(username=username).exists():
                raise ValidationError("El nombre de usuario ya existe")
            if User.objects.filter(email=email).exists():
                raise ValidationError("El correo electrónico ya existe")
            user = User.objects.create_user(username=username, email=email, password=password)
            return user

        def authenticate_user(self, username: str, password: str) -> User:
            user = authenticate(username=username, password=password)
            if not user:
                raise ValidationError("Credenciales inválidas")
            return user

        def logout_user(self, request) -> None:
            logout(request)
    ```
- **Formularios (`adapters/forms.py`)**:
  - Define formularios para registro e inicio de sesión.
  - Ejemplo:
    ```python
    from django import forms
    from django.core.exceptions import ValidationError

    class RegisterForm(forms.Form):
        username = forms.CharField(max_length=150, required=True)
        email = forms.EmailField(required=True)
        password = forms.CharField(widget=forms.PasswordInput, min_length=8, required=True)

        def clean_username(self):
            username = self.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                raise ValidationError("El nombre de usuario ya existe")
            return username

        def clean_email(self):
            email = self.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                raise ValidationError("El correo electrónico ya existe")
            return email

    class LoginForm(forms.Form):
        username = forms.CharField(max_length=150, required=True)
        password = forms.CharField(widget=forms.PasswordInput, required=True)
    ```
- **Vistas (`adapters/views.py`)**:
  - Implementa vistas de clase para manejar las solicitudes HTTP.
  - Ejemplo:
    ```python
    from django.views import View
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from ..domain.use_cases import RegisterUserUseCase, LoginUserUseCase, LogoutUserUseCase
    from .forms import RegisterForm, LoginForm
    from .repository import DjangoAuthRepository

    class RegisterView(View):
        def get(self, request):
            form = RegisterForm()
            return render(request, 'auth/register.html', {'form': form})

        def post(self, request):
            form = RegisterForm(request.POST)
            if form.is_valid():
                use_case = RegisterUserUseCase(DjangoAuthRepository())
                success = use_case.execute(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                if success:
                    return redirect('core_auth:login')
            return render(request, 'auth/register.html', {'form': form})

    class LoginView(View):
        def get(self, request):
            form = LoginForm()
            return render(request, 'auth/login.html', {'form': form})

        def post(self, request):
            form = LoginForm(request.POST)
            if form.is_valid():
                use_case = LoginUserUseCase(DjangoAuthRepository())
                success = use_case.execute(
                    request,
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password']
                )
                if success:
                    return redirect('core_app:home')  # Asumiendo que core_app tiene una URL 'home'
            return render(request, 'auth/login.html', {'form': form, 'error': 'Credenciales inválidas'})

    class LogoutView(View):
        def get(self, request):
            use_case = LogoutUserUseCase(DjangoAuthRepository())
            use_case.execute(request)
            return render(request, 'auth/logout.html')

        def post(self, request):
            use_case = LogoutUserUseCase(DjangoAuthRepository())
            use_case.execute(request)
            return redirect('core_auth:login')
    ```

### 6. Crear Plantillas HTML con Tailwind CSS
- **Plantilla Base (`templates/auth/base.html`)**:
  - Define la estructura básica con Tailwind CSS.
  - Ejemplo:
    ```html
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{% block title %}DjangoProyects{% endblock %}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto p-4">
            {% block content %}
            {% endblock %}
        </div>
    </body>
    </html>
    ```
- **Formulario de Inicio de Sesión (`templates/auth/login.html`)**:
  - Formulario estilizado con Tailwind, con manejo de errores.
  - Ejemplo:
    ```html
    {% extends 'auth/base.html' %}
    {% block title %}Iniciar Sesión{% endblock %}
    {% block content %}
    <div class="max-w-md mx-auto mt-10 bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-6 text-center">Iniciar Sesión</h2>
        {% if error %}
        <p class="text-red-500 mb-4">{{ error }}</p>
        {% endif %}
        <form method="post" class="space-y-4">
            {% csrf_token %}
            <div>
                <label for="{{ form.username.id_for_label }}" class="block text-sm font-medium text-gray-700">Usuario</label>
                <input type="text" name="{{ form.username.name }}" id="{{ form.username.id_for_label }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
                {% if form.username.errors %}
                <p class="text-red-500 text-sm">{{ form.username.errors }}</p>
                {% endif %}
            </div>
            <div>
                <label for="{{ form.password.id_for_label }}" class="block text-sm font-medium text-gray-700">Contraseña</label>
                <input type="password" name="{{ form.password.name }}" id="{{ form.password.id_for_label }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
                {% if form.password.errors %}
                <p class="text-red-500 text-sm">{{ form.password.errors }}</p>
                {% endif %}
            </div>
            <button type="submit" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700">Iniciar Sesión</button>
        </form>
        <p class="mt-4 text-center">
            ¿No tienes cuenta? <a href="{% url 'core_auth:register' %}" class="text-indigo-600 hover:underline">Regístrate</a>
        </p>
    </div>
    {% endblock %}
    ```
- **Formulario de Registro (`templates/auth/register.html`)**:
  - Formulario estilizado con Tailwind, con validaciones.
  - Ejemplo:
    ```html
    {% extends 'auth/base.html' %}
    {% block title %}Registrarse{% endblock %}
    {% block content %}
    <div class="max-w-md mx-auto mt-10 bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-6 text-center">Registrarse</h2>
        <form method="post" class="space-y-4">
            {% csrf_token %}
            <div>
                <label for="{{ form.username.id_for_label }}" class="block text-sm font-medium text-gray-700">Usuario</label>
                <input type="text" name="{{ form.username.name }}" id="{{ form.username.id_for_label }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
                {% if form.username.errors %}
                <p class="text-red-500 text-sm">{{ form.username.errors }}</p>
                {% endif %}
            </div>
            <div>
                <label for="{{ form.email.id_for_label }}" class="block text-sm font-medium text-gray-700">Correo Electrónico</label>
                <input type="email" name="{{ form.email.name }}" id="{{ form.email.id_for_label }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" required>
                {% if form.email.errors %}
                <p class="text-red-500 text-sm">{{ form.email.errors }}</p>
                {% endif %}
            </div>
            <div>
                <label for="{{ form.password.id_for_label }}" class="block text-sm font-medium text-gray-700">Contraseña</label>
                <input type="password" name="{{ form.password.name }}" id="{{ form.password.id_for_label }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" minlength="8" required>
                {% if form.password.errors %}
                <p class="text-red-500 text-sm">{{ form.password.errors }}</p>
                {% endif %}
            </div>
            <button type="submit" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700">Registrarse</button>
        </form>
        <p class="mt-4 text-center">
            ¿Ya tienes cuenta? <a href="{% url 'core_auth:login' %}" class="text-indigo-600 hover:underline">Inicia Sesión</a>
        </p>
    </div>
    {% endblock %}
    ```
- **Página de Cierre de Sesión (`templates/auth/logout.html`)**:
  - Página simple para confirmar el cierre de sesión.
  - Ejemplo:
    ```html
    {% extends 'auth/base.html' %}
    {% block title %}Cerrar Sesión{% endblock %}
    {% block content %}
    <div class="max-w-md mx-auto mt-10 bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-bold mb-6 text-center">Cerrar Sesión</h2>
        <p class="text-gray-700 mb-4">Has cerrado sesión correctamente.</p>
        <a href="{% url 'core_auth:login' %}" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 text-center inline-block">Volver a Iniciar Sesión</a>
    </div>
    {% endblock %}
    ```

### 7. Configurar Pruebas
- Crear pruebas en `tests/test_use_cases.py` para los casos de uso, usando mocks para simular el repositorio.
- Crear pruebas en `tests/test_adapters.py` para formularios, vistas y el repositorio.
- Ejemplo de pruebas:
  ```python
  from django.test import TestCase, RequestFactory
  from django.contrib.auth.models import User
  from ..domain.use_cases import RegisterUserUseCase, LoginUserUseCase, LogoutUserUseCase
  from ..adapters.repository import DjangoAuthRepository
  from ..adapters.forms import RegisterForm, LoginForm
  from unittest.mock import Mock

  class RegisterUseCaseTest(TestCase):
      def test_register_success(self):
          mock_repo = Mock()
          mock_repo.create_user.return_value = User(username='testuser', email='test@example.com')
          use_case = RegisterUserUseCase(mock_repo)
          result = use_case.execute('testuser', 'test@example.com', 'password123')
          self.assertTrue(result)
          mock_repo.create_user.assert_called_once_with('testuser', 'test@example.com', 'password123')

  class LoginFormTest(TestCase):
      def test_valid_form(self):
          form_data = {'username': 'testuser', 'password': 'password123'}
          form = LoginForm(data=form_data)
          self.assertTrue(form.is_valid())
  ```
- Ejecutar pruebas con:
  ```bash
  pytest --cov=src/core_auth --cov-report=html
  ```

### 8. Actualizar Documentación
- Actualiza `README.md` para incluir instrucciones específicas para `core_auth`:
  - Configuración de URLs y vistas.
  - Uso de las plantillas HTML.
  - Ejecución de migraciones para la base de datos por defecto.
- Actualiza `status.md` para reflejar el estado completado de la autenticación básica:
  ```markdown
  ### Autenticación Vanilla de Django
  - ✅ **Configuración Básica**: Correctamente configurada
  - ✅ **Modelo de Usuario**: Usando el modelo por defecto de Django
  - ✅ **URLs de Autenticación**: Definidas en `core_auth/adapters/urls.py`
  - ✅ **Vistas y Plantillas**: Implementadas con Tailwind CSS
  ```

### 9. Verificaciones Finales
- Asegúrate de que `.gitignore` incluya archivos sensibles:
  ```
  .env
  data/*.sqlite3
  __pycache__/
  ```
- Verifica que las migraciones estén aplicadas:
  ```bash
  python manage.py migrate --database=default
  ```
- Prueba la funcionalidad manualmente:
  - Accede a `/auth/register/` y registra un usuario.
  - Accede a `/auth/login/` e inicia sesión.
  - Accede a `/auth/logout/` y cierra sesión.
- Verifica la cobertura de pruebas con `pytest-cov`.

## Tiempo Estimado
- **Configuración de URLs, puertos y adaptadores**: 1 día.
- **Implementación de casos de uso y vistas**: 1 día.
- **Creación de plantillas HTML con Tailwind**: 1 día.
- **Escritura de pruebas**: 1 día.
- **Actualización de documentación**: 0.5 días.
- **Total**: 4.5 días.

## Notas Adicionales
- Las plantillas HTML usan Tailwind CSS directamente, sin archivos `.css` externos, siguiendo las especificaciones del proyecto.
- La autenticación básica no depende de `django-allauth`, pero se integra con la configuración existente para permitir futura autenticación social.
- Las redirecciones asumen que `core_app` tiene una URL `home`. Si no existe, ajusta la redirección a una URL válida (ej. `/`).
- Mantén las configuraciones sensibles en `.env` y usa `.env.example` para guiar a los desarrolladores.