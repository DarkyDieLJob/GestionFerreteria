from abc import ABC, abstractmethod
from typing import Optional
from django.contrib.auth.models import User
from django.http import HttpRequest


class Core_authRepository(ABC):
    @abstractmethod
    def save(self, data):  # pragma: no cover
        pass

    @abstractmethod
    def get_all(self):  # pragma: no cover
        pass


class AuthRepository(ABC):
    """
    Interface para el manejo de la autenticación de usuarios.
    Define los métodos que deben ser implementados por cualquier adaptador de autenticación.
    """
    
    @abstractmethod
    def create_user(self, username: str, email: str, password: str) -> User:  # pragma: no cover
        """
        Crea un nuevo usuario en el sistema.
        
        Args:
            username: Nombre de usuario único
            email: Correo electrónico del usuario
            password: Contraseña en texto plano
            
        Returns:
            User: Instancia del usuario creado
            
        Raises:
            ValueError: Si el usuario no puede ser creado (ej: usuario/email ya existe)
        """
        pass
    
    @abstractmethod
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:  # pragma: no cover
        """
        Autentica un usuario con nombre de usuario/email y contraseña.
        
        Args:
            username_or_email: Nombre de usuario o correo electrónico
            password: Contraseña en texto plano
            
        Returns:
            User: Instancia del usuario autenticado si las credenciales son válidas
            None: Si las credenciales son inválidas
        """
        pass
    
    @abstractmethod
    def logout_user(self, request: HttpRequest) -> None:  # pragma: no cover
        """
        Cierra la sesión del usuario actual.
        
        Args:
            request: Objeto HttpRequest de Django
        """
        pass