from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Core_app

@login_required
def home(request):
    """
    Vista de inicio que muestra un mensaje de bienvenida con los datos del usuario.
    Requiere que el usuario esté autenticado.
    """
    user = request.user
    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'last_login': user.last_login,
        'date_joined': user.date_joined,
    }
    return render(request, 'core_app/home.html', context)