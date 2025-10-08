"""
Vistas de la app "articulos" (capa de adaptadores) usando arquitectura hexagonal.

Estas vistas delegan la lógica de negocio a casos de uso del dominio para
mantener el desacople entre Django y la lógica pura de Python.
"""

from typing import Any, Dict, List

from django.apps import apps
from django.shortcuts import redirect, render
from django.views.generic import ListView

from ..domain.use_cases import BuscarArticuloUseCase, MapearArticuloUseCase
from .repository import BusquedaRepository, MapeoRepository
from .forms import MapearArticuloForm


class BuscarArticuloView(ListView):
    """
    Vista de búsqueda que utiliza el caso de uso BuscarArticuloUseCase.

    - template_name: articulos/buscar_articulos.html
    - context_object_name: "resultados"

    Los resultados pueden incluir entradas provenientes de:
      - PrecioDeLista
      - ArticuloSinRevisar
      - ArticuloProveedor
    """

    template_name = "articulos/buscar_articulos.html"
    context_object_name = "resultados"

    def get_queryset(self) -> List[Dict[str, Any]]:  # type: ignore[override]
        query = self.request.GET.get("q", "")
        use_case = BuscarArticuloUseCase(BusquedaRepository())
        return use_case.execute(query=query)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


def mapear_articulo(request, pendiente_id: int):
    """
    Vista de función para mapear un ArticuloSinRevisar hacia un Articulo existente.

    Flujo:
    - GET: muestra una página con los datos del pendiente y una descripción sugerida.
    - POST: procesa el formulario (p.ej. codigo_barras, descripcion); crea o actualiza
      un Articulo y ejecuta el mapeo mediante MapearArticuloUseCase. Finalmente
      redirige a la búsqueda de artículos.
    """

    Articulo = apps.get_model("articulos", "Articulo")
    ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")

    pendiente = ArticuloSinRevisar.objects.select_related("proveedor", "descuento").get(pk=pendiente_id)

    if request.method == "POST":
        # Integración con forms: validar datos del POST con MapearArticuloForm
        form = MapearArticuloForm(request.POST)
        if form.is_valid():
            codigo_barras = (form.cleaned_data.get("codigo_barras") or "").strip()
            descripcion = (form.cleaned_data.get("descripcion") or "").strip() or pendiente.descripcion_proveedor
            articulo_id = (form.cleaned_data.get("articulo_id") or "").strip()

            # Usar artículo existente si se seleccionó
            if articulo_id:
                art = Articulo.objects.get(pk=articulo_id)
            else:
                if codigo_barras:
                    art, _created = Articulo.objects.get_or_create(
                        codigo_barras=codigo_barras,
                        defaults={"descripcion": descripcion},
                    )
                    if not _created and descripcion and getattr(art, "descripcion", None) != descripcion:
                        art.descripcion = descripcion
                        art.save()
                else:
                    art = Articulo.objects.create(descripcion=descripcion)

            # Ejecutar caso de uso de mapeo (adaptador MapeoRepository).
            # Nota: el caso de uso aún invoca el puerto con 'usuario_id', se adapta localmente.
            class _MapeoRepoAdapter:
                def mapear_articulo(self, *, articulo_s_revisar_id, articulo_id, usuario_id=None):  # type: ignore[override]
                    repo = MapeoRepository()
                    return repo.mapear_articulo(
                        articulo_s_revisar_id=articulo_s_revisar_id,
                        articulo_id=articulo_id,
                    )

            use_case = MapearArticuloUseCase(_MapeoRepoAdapter())
            use_case.execute(articulo_s_revisar_id=pendiente.id, articulo_id=art.id, usuario_id=None)

            # Volver a la búsqueda
            return redirect("articulos:buscar_articulos")
        else:
            # Form inválido: continuar para renderizar errores
            pass

        # Ejecutar caso de uso de mapeo (adaptador MapeoRepository).
        # Nota: el caso de uso aún invoca el puerto con 'usuario_id',
        # por lo que definimos un pequeño adaptador que acepta ese argumento
        # y lo ignora delegando al repositorio real.

        class _MapeoRepoAdapter:
            def mapear_articulo(self, *, articulo_s_revisar_id, articulo_id, usuario_id=None):  # type: ignore[override]
                repo = MapeoRepository()
                return repo.mapear_articulo(
                    articulo_s_revisar_id=articulo_s_revisar_id,
                    articulo_id=articulo_id,
                )

        use_case = MapearArticuloUseCase(_MapeoRepoAdapter())
        use_case.execute(articulo_s_revisar_id=pendiente.id, articulo_id=art.id, usuario_id=None)  # usuario_id no usado

        # Volver a la búsqueda
        return redirect("articulos:buscar_articulos")

    # GET: mostrar plantilla con datos del pendiente y sugerencia de descripción
    # GET: inicializar formulario con descripción sugerida; en POST, reutilizar form si existe
    if request.method == "GET":
        form = MapearArticuloForm(initial={"descripcion": pendiente.descripcion_proveedor})
    else:
        form = locals().get("form") or MapearArticuloForm()

    contexto = {
        "pendiente": pendiente,
        "descripcion_sugerida": pendiente.descripcion_proveedor,
        "codigo_sugerido": f"{pendiente.codigo_proveedor}/{pendiente.proveedor.abreviatura}",
        # Proveer el modelo para que la plantilla pueda iterar Articulo.objects.all
        "Articulo": apps.get_model("articulos", "Articulo"),
        # Proveer el formulario para renderizado/errores
        "form": form,
    }
    return render(request, "articulos/mapear_articulo.html", contexto)