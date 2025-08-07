# Interfaces para el dominio
# templates/app_template/ports/interfaces.py
from abc import ABC, abstractmethod

class Core_authRepository(ABC):
    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def get_all(self):
        pass