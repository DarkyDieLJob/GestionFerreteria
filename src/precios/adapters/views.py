# Archivo de vistas del adaptador
"""
Vistas de la app precios (capa adapters) siguiendo arquitectura hexagonal.

Notas:
- Estas vistas operan explícitamente contra la base de datos 'negocio_db',
  respetando los routers/aliases definidos en core_config (ver database_routers.py).
- Los nombres de URL están namespaced bajo 'precios' y se usan con reverse,
  por ejemplo: reverse('precios:descuento_list').
"""

from typing import Any, Dict

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from precios.adapters.models import Descuento, PrecioDeLista
from precios.adapters.forms import DescuentoForm  # Integración con formularios (ModelForm)


class DescuentoListView(ListView):
    """Lista de descuentos.

    - Usa la base de datos 'negocio_db' para leer.
    - Permite una búsqueda opcional por 'tipo' vía querystring 'q'.
    """

    model = Descuento
    template_name = "precios/descuento_list.html"
    context_object_name = "descuentos"

    def get_queryset(self):
        # Base: todos los descuentos desde la DB de negocio
        qs = Descuento.objects.using("negocio_db").all()
        # Búsqueda opcional por tipo
        q = (self.request.GET.get("q", "") or "").strip()
        if q:
            qs = qs.filter(tipo__icontains=q)
        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["q"] = (self.request.GET.get("q", "") or "").strip()
        # Alias para plantillas que esperan 'query'
        context["query"] = context["q"]
        return context


class DescuentoCreateView(CreateView):
    """Crear un descuento.

    - Guarda explícitamente en 'negocio_db'.
    - Redirige a la lista al finalizar.
    """

    model = Descuento
    template_name = "precios/descuento_form.html"
    # Usar el ModelForm declarado en adapters/forms.py
    form_class = DescuentoForm
    success_url = reverse_lazy("precios:descuento_list")

    def form_valid(self, form):
        # Guardar en la base de datos de negocio explícitamente
        self.object = form.save(commit=False)
        self.object.save(using="negocio_db")
        # Si hubiera M2M, se requeriría guardarlas manualmente; no aplica aquí
        return redirect(self.get_success_url())


class DescuentoUpdateView(UpdateView):
    """Editar un descuento.

    - Consulta y guarda usando 'negocio_db'.
    - Reutiliza la misma plantilla y campos del create.
    """

    model = Descuento
    template_name = "precios/descuento_form.html"
    # Usar el mismo ModelForm para edición
    form_class = DescuentoForm
    success_url = reverse_lazy("precios:descuento_list")

    def get_queryset(self):
        # Asegura que el objeto a editar provenga de 'negocio_db'
        return Descuento.objects.using("negocio_db").all()

    def form_valid(self, form):
        # Guardar cambios en la base negocio
        self.object = form.save(commit=False)
        self.object.save(using="negocio_db")
        return redirect(self.get_success_url())


class DescuentoDeleteView(DeleteView):
    """Eliminar un descuento.

    - Consulta contra 'negocio_db'.
    - Tras eliminar, redirige a la lista.
    """

    model = Descuento
    template_name = "precios/descuento_confirm_delete.html"
    success_url = reverse_lazy("precios:descuento_list")

    def get_queryset(self):
        # Asegura que el objeto a eliminar provenga de 'negocio_db'
        return Descuento.objects.using("negocio_db").all()