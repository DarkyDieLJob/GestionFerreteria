# Archivo de vistas del adaptador
"""
Vistas (adaptadores) para la app proveedores.

Estas vistas usan la base de datos 'negocio_db' explícitamente para
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
    """Listado de proveedores usando la BD 'negocio_db'.

    - Template: proveedores/proveedor_list.html
    - Contexto: "proveedores" (queryset), y "q" (término de búsqueda)
    - Búsqueda opcional por 'nombre' o 'abreviatura' con parámetro GET 'q'
    """

    model = Proveedor
    template_name = "proveedores/proveedor_list.html"
    context_object_name = "proveedores"

    def get_queryset(self):
        qs = Proveedor.objects.using("negocio_db").all()
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
    """Creación de proveedor en la BD 'negocio_db'."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProveedorForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def form_valid(self, form):
        # Guardar explícitamente en la base 'negocio_db'
        self.object = form.save(commit=False)
        self.object.save(using="negocio_db")
        # Si hubiera M2M en el futuro, requeriría un guardado adicional sobre la BD por defecto;
        # aquí no hay M2M en los campos del formulario, por lo que no se invoca save_m2m.
        return redirect(self.get_success_url())


class ProveedorUpdateView(UpdateView):
    """Edición de proveedor usando y guardando en 'negocio_db'."""

    model = Proveedor
    template_name = "proveedores/proveedor_form.html"
    # Integración con formularios: usar ProveedorForm para centralizar validaciones
    form_class = ProveedorForm
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        # Consultar objetos desde 'negocio_db'
        return Proveedor.objects.using("negocio_db").all()

    def form_valid(self, form):
        # Guardar cambios explícitamente en 'negocio_db'
        self.object = form.save(commit=False)
        self.object.save(using="negocio_db")
        return redirect(self.get_success_url())


class ProveedorDeleteView(DeleteView):
    """Eliminación de proveedor usando 'negocio_db'."""

    model = Proveedor
    template_name = "proveedores/proveedor_confirm_delete.html"
    success_url = reverse_lazy("proveedores:proveedor_list")

    def get_queryset(self):
        # Consultar objetos desde 'negocio_db'
        return Proveedor.objects.using("negocio_db").all()

    def delete(self, request, *args, **kwargs):
        # Eliminar explícitamente en 'negocio_db'
        self.object = self.get_object()
        self.object.delete(using="negocio_db")
        return redirect(self.get_success_url())