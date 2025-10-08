# Archivo de vistas del adaptador
"""
Vistas (adaptadores) para la app proveedores.

Estas vistas actúan como adaptadores en la arquitectura hexagonal del
proyecto: coordinan la interacción con Django mientras la lógica de negocio
permanece en `domain/`. Todas las operaciones usan la base de datos por
defecto.
"""

from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from proveedores.models import Contacto, ContactoProveedor, Proveedor
from proveedores.adapters.forms import ProveedorForm


class ProveedorListView(ListView):
    """Listado de proveedores utilizando la base de datos por defecto.

    - Template: `proveedores/proveedor_list.html`
    - Contexto: "proveedores" (queryset) y "q" (término de búsqueda)
    - Búsqueda opcional por nombre o abreviatura mediante parámetro GET `q`
    """

    model = Proveedor
    template_name = "proveedores/proveedor_list.html"
    context_object_name = "proveedores"

    def get_queryset(self):
        qs = Proveedor.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(abreviatura__icontains=q))
        return qs

class ProveedorCreateView(CreateView):
    """Creación de proveedor."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProveedorForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def form_valid(self, form):
        self.object = form.save()
        return redirect(self.get_success_url())

class ProveedorUpdateView(UpdateView):
    """Edición de proveedor."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProvealForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        return Proveedor.objects.all()

    def form_valid(self, form):
        self.object = form.save()
        return redirect(self.get_success_url())

class ProveedorDeleteView(DeleteView):
    """Eliminación de proveedor."""

    model = Proveedor
    template_name = "proveedores/proveedor_confirm_delete.html"
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        return Proveedor.objects.all()

    def delete(self, request, *args, **kwargs):
        proveedor = self.get_object()
        proveedor.delete()
        return redirect(self.success_url)