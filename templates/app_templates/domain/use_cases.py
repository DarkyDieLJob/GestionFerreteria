# Lógica de negocio pura (casos de uso)
# templates/app_template/domain/use_cases.py
class {{ app_name|capfirst }}UseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, data):
        # Ejemplo de caso de uso
        return self.repository.save(data)