# Archivo de vistas del adaptador
"""
Vistas de la app precios (capa adapters) siguiendo arquitectura hexagonal.

Notas:
 - Estas vistas operan contra la base de datos por defecto.
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

    - Usa la base de datos por defecto para leer.
    - Permite una búsqueda opcional por 'tipo' vía querystring 'q'.
    """

    model = Descuento
    template_name = "precios/descuento_list.html"
    context_object_name = "descuentos"

    def get_queryset(self):
        # Base: todos los descuentos desde la DB por defecto
        qs = Descuento.objects.all()
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

    - Guarda en la base por defecto.
    - Redirige a la lista al finalizar.
    """

    model = Descuento
    template_name = "precios/descuento_form.html"
    # Usar el ModelForm declarado en adapters/forms.py
    form_class = DescuentoForm
    success_url = reverse_lazy("precios:descuento_list")

    def form_valid(self, form):
        # Guardar en la base de datos por defecto
        self.object = form.save(commit=False)
        self.object.save()
        # Si hubiera M2M, se requeriría guardarlas manualmente; no aplica aquí
        return redirect(self.get_success_url())


class DescuentoUpdateView(UpdateView):
    """Editar un descuento.

    - Consulta y guarda usando la base por defecto.
    - Reutiliza la misma plantilla y campos del create.
    """

    model = Descuento
    template_name = "precios/descuento_form.html"
    # Usar el mismo ModelForm para edición
    form_class = DescuentoForm
    success_url = reverse_lazy("precios:descuento_list")

    def get_queryset(self):
        # Asegura que el objeto a editar provenga de la base por defecto
        return Descuento.objects.all()

    def form_valid(self, form):
        # Guardar cambios en la base por defecto
        self.object = form.save(commit=False)
        self.object.save()
        return redirect(self.get_success_url())


class DescuentoDeleteView(DeleteView):
    """Eliminar un descuento.

    - Consulta contra la base por defecto.
    - Tras eliminar, redirige a la lista.
    """

    model = Descuento
    template_name = "precios/descuento_confirm_delete.html"
    success_url = reverse_lazy("precios:descuento_list")

    def get_queryset(self):
        # Asegura que el objeto a eliminar provenga de la base por defecto
        return Descuento.objects.all()