import os

# Define la estructura de directorios y archivos
template_dir = 'app_templates/core_app_template'
app_name = 'core_app'

# Lista de directorios a crear. Los diccionarios se usan para archivos con contenido.
structure = {
    app_name: {
        '__init__.py': '',
        'adapters': {
            '__init__.py': '',
            'models.py': '# Archivo de modelos del adaptador',
            'repository.py': '# Archivo del repositorio del adaptador',
            'serializers.py': '# Archivo de serializadores del adaptador',
            'views.py': '# Archivo de vistas del adaptador',
            'urls.py': """from django.urls import path
from . import views

app_name = '{{ app_name }}'

urlpatterns = [
    # path('', views.article_list, name='article_list'),
]""",
        },
        'config.py': '# Configuración de la base de datos específica de la app',
        'domain': {
            '__init__.py': '',
            'use_cases.py': '# Lógica de negocio pura (casos de uso)',
        },
        'ports': {
            '__init__.py': '',
            'interfaces.py': '# Interfaces para el dominio',
        },
        'templates': {
            'base.html': '',
            'auth': {
                'login.html': '',
                'register.html': '',
            },
        },
        'tests': {
            '__init__.py': '',
            'test_adapters.py': '# Pruebas para los adaptadores',
            'test_use_cases.py': '# Pruebas para los casos de uso del dominio',
        },
        'apps.py': f'''from django.apps import AppConfig

class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'
''',
    }
}

def create_structure(base_path, structure_dict):
    """
    Crea recursivamente directorios y archivos a partir de un diccionario.
    """
    for key, value in structure_dict.items():
        current_path = os.path.join(base_path, key)
        
        if isinstance(value, dict):
            # Es un directorio, lo crea y llama recursivamente
            os.makedirs(current_path, exist_ok=True)
            print(f'Directorio creado: {current_path}')
            create_structure(current_path, value)
        else:
            # Es un archivo, lo crea y escribe el contenido
            with open(current_path, 'w') as f:
                f.write(value)
            print(f'Archivo creado: {current_path}')

if __name__ == '__main__':
    print(f'Creando estructura de plantilla en: {template_dir}')
    os.makedirs(template_dir, exist_ok=True)
    create_structure(template_dir, structure)
    print('\n¡Plantilla de aplicación creada con éxito!')
    print(f'\nAhora puedes usarla con el comando:')
    print(f'python manage.py startapp <nombre_de_la_app> --template={template_dir}')