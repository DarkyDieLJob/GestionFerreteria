# Archivo de vistas del adaptador
"""
Vistas (adaptadores) para la app proveedores.

Estas vistas usan la base de datos por defecto para
consultas y escrituras, respetando la arquitectura hexagonal del proyecto:
la lógica de negocio debería vivir en domain/, y los adaptadores (como
estas vistas) coordinan entradas/salidas con Django.
"""

from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from proveedores.models import Contacto, ContactoProveedor, Proveedor
from proveedores.adapters.forms import ProveedorForm


class ProveedorListView(ListView):
    """Listado de proveedores usando la BD por defecto.

    - Template: proveedores/proveedor_list.html
    - Contexto: "proveedores" (queryset), y "q" (término de búsqueda)
    - Búsqueda opcional por 'nombre' o 'abreviatura' con parámetro GET 'q'
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        # Alias para plantillas que esperan 'query'
        context["query"] = context["q"]
        return context


class ProveedorCreateView(CreateView):
    """Creación de proveedor en la BD por defecto."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProveedorForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def form_valid(self, form):
        # Guardar en la base por defecto
        self.object = form.save(commit=False)
        self.object.save()
        # Si hubiera M2M en el futuro, requeriría un guardado adicional sobre la BD por defecto;
        # aquí no hay M2M en los campos del formulario, por lo que no se invoca save_m2m.
        return redirect(self.get_success_url())


class ProveedorUpdateView(UpdateView):
    """Edición de proveedor usando y guardando en la BD por defecto."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProveedorForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        # Consultar objetos desde la BD por defecto
        return Proveedor.objects.all()

    def form_valid(self, form):
        # Guardar cambios en la BD por defecto
        self.object = form.save(commit=False)
        self.object.save()
        return redirect(self.get_success_url())


class ProveedorDeleteView(DeleteView):
    """Eliminación de proveedor usando la BD por defecto."""

    model = Proveedor
    template_name = "proveedores/proveedor_confirm_delete.html"
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        # Consultar objetos desde la BD por defecto
        return Proveedor.objects.all()

    def delete(self, request, *args, **kwargs):
        # Eliminar en la BD por defecto
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.get_success_url())