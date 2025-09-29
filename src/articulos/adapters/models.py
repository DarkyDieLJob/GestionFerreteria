from django.db import models
from django.apps import apps
from django.conf import settings
from decimal import Decimal
from articulos.domain.pricing import calculate_prices


class ArticuloBase(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    # Relación correcta: un Descuento puede asociarse a muchos ArticuloBase (uno a muchos)
    descuento = models.ForeignKey('precios.Descuento', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

    def generar_precios(self, precio_de_lista, cantidad=1, pago_efectivo=False, dividir=False, bulto=1, iva=0, descuento_override=None, proveedor_override=None):
        """Genera precios dinámicos delegando en el calculador de dominio.
        Nota: el umbral/cantidad_bulto no participa del cálculo actual; el bulto del artículo sí.
        """
        config = descuento_override if descuento_override is not None else self.get_descuento()
        proveedor = proveedor_override if proveedor_override is not None else self.get_proveedor()

        result = calculate_prices(
            precio_de_lista=precio_de_lista,
            iva=iva,
            proveedor_desc_com=getattr(proveedor, 'descuento_comercial', 0),
            proveedor_margen=getattr(proveedor, 'margen_ganancia', 1),
            proveedor_margen_ef=getattr(proveedor, 'margen_ganancia_efectivo', 1),
            descuento_general=getattr(config, 'general', 0),
            descuento_activo=getattr(config, 'is_active', lambda: True)(),
            descuento_bulto=getattr(config, 'bulto', 0),
            descuento_cantidad_bulto=getattr(config, 'cantidad_bulto', 1),
            bulto_articulo=bulto or 1,
            cantidad=cantidad,
            dividir=dividir,
            debug=getattr(settings, 'DEBUG_INFO', False),
        )

        # Mantener compatibilidad: incluir campos debug adicionales si DEBUG_INFO
        if getattr(settings, 'DEBUG_INFO', False):
            result.setdefault('debug_bulto_articulo', int(bulto or 1))
            result.setdefault('debug_cantidad', float(cantidad))
        return result

    def get_descuento(self):
        """Devuelve el Descuento activo asociado al ArticuloBase.
        Prioriza el FK en la propia instancia. Si no hay, intenta compatibilidad
        con FKs históricas (p.ej., en ASR o en AP) y por último usa 'Sin Descuento'.
        """
        Descuento = apps.get_model('precios', 'Descuento')
        # 1) FK en ArticuloBase (nuevo modelo de datos)
        if getattr(self, 'descuento_id', None):
            try:
                obj = Descuento.objects.using('default').get(pk=self.descuento_id)
                if getattr(obj, 'is_active', lambda: True)():
                    return obj
            except Descuento.DoesNotExist:
                pass
        # 2) Compatibilidad: si el modelo concreto tenía FK propia 'descuento'
        try:
            own_fk = super().descuento  # may not exist; defensive
        except Exception:
            own_fk = None
        if own_fk:
            try:
                if self.descuento and self.descuento.is_active():
                    return self.descuento
            except Exception:
                pass
        # 3) Compatibilidad: tomar del primer ArticuloProveedor relacionado si está activo
        try:
            ap = getattr(self, 'articuloproveedor_set', None)
            if ap is not None and ap.exists():
                ap0 = ap.first()
                if getattr(ap0, 'descuento', None) and ap0.descuento and ap0.descuento.is_active():
                    return ap0.descuento
        except Exception:
            pass
        # 4) Default: 'Sin Descuento' (no crear aquí para evitar locks en tests)
        try:
            return Descuento.objects.using('default').get(tipo="Sin Descuento")
        except Descuento.DoesNotExist:
            # Devolver instancia no persistida como configuración por defecto
            return Descuento(
                tipo="Sin Descuento",
                temporal=False,
                general=0.0,
                bulto=0.0,
                cantidad_bulto=5,
            )

    def get_proveedor(self):
        raise NotImplementedError

class Articulo(ArticuloBase):
    codigo_barras = models.CharField(max_length=50, unique=True)
    des_acumulada = models.TextField(blank=True)
    stock_consolidado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imagen = models.ImageField(upload_to='articulos/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['codigo_barras'])
        ]

    def get_descuento(self):
        # Delegar en la implementación unificada del base
        return super().get_descuento()

    def get_proveedor(self):
        return self.articuloproveedor_set.first().proveedor if self.articuloproveedor_set.exists() else None

    def generar_precios(self, cantidad=1, pago_efectivo=False):
        ap = self.articuloproveedor_set.first()
        if not ap:
            return {'error': 'No hay proveedor asociado'}
        return super().generar_precios(
            precio_de_lista=ap.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=ap.dividir,
            bulto=ap.precio_de_lista.bulto,
            iva=ap.precio_de_lista.iva
        )

class ArticuloSinRevisar(ArticuloBase):
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    codigo_proveedor = models.CharField(max_length=50)  # e.g., '37/', '0037-25/'
    descripcion_proveedor = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('mapeado', 'Mapeado'), ('nuevo', 'Nuevo')])
    fecha_mapeo = models.DateTimeField(null=True, blank=True)
    # Campo 'usuario' eliminado: no es necesario para la importación ni el mapeo y
    # simplifica la relación, evitando dependencia con auth_user en la base 'default'.

    class Meta:
        indexes = [
            models.Index(fields=['proveedor', 'codigo_proveedor']),
            models.Index(fields=['estado']),
            models.Index(fields=['codigo_barras'])
        ]

    def save(self, *args, **kwargs):
        codigo_base = self.codigo_proveedor.rstrip('/')
        try:
            codigo_base = str(int(codigo_base.lstrip('0')))
        except ValueError:
            pass
        self.codigo_proveedor = f"{codigo_base}/"
        # Asignar descuento por defecto si no se proporcionó, sin crear en DB
        if not getattr(self, 'descuento', None):
            Descuento = apps.get_model('precios', 'Descuento')
            try:
                self.descuento = Descuento.objects.using('default').get(tipo="Sin Descuento")
            except Descuento.DoesNotExist:
                # No asignar si no existe; ArticuloBase.get_descuento manejará valor por defecto
                pass
        super().save(*args, **kwargs)

    def get_descuento(self):
        # Delegar en la implementación unificada del base
        return super().get_descuento()

    def get_proveedor(self):
        # Forzar lectura desde DB para coherencia de pruebas de performance
        from proveedores.adapters.models import Proveedor
        try:
            return Proveedor.objects.using('default').get(pk=self.proveedor_id)
        except Proveedor.DoesNotExist:
            return None

    def generar_precios(self, cantidad=1, pago_efectivo=False, **kwargs):
        # Permitir overrides desde ArticuloProveedor
        precio_de_lista = kwargs.pop('precio_de_lista', self.precio)
        dividir = kwargs.pop('dividir', False)  # ArticuloSinRevisar no usa dividir por defecto
        bulto = kwargs.pop('bulto', 1)
        iva = kwargs.pop('iva', 0)
        descuento_override = kwargs.pop('descuento_override', None)
        proveedor_override = kwargs.pop('proveedor_override', None)
        # Cualquier otro kwarg se ignora para mantener compatibilidad
        return super().generar_precios(
            precio_de_lista=precio_de_lista,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=dividir,
            bulto=bulto,
            iva=iva,
            descuento_override=descuento_override,
            proveedor_override=proveedor_override,
        )

class ArticuloProveedor(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, null=True, blank=True)
    articulo_s_revisar = models.ForeignKey(ArticuloSinRevisar, on_delete=models.CASCADE, null=True, blank=True)
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    precio_de_lista = models.ForeignKey('precios.PrecioDeLista', on_delete=models.CASCADE)
    codigo_proveedor = models.CharField(max_length=50)  # e.g., '37/', '0037-25/'
    descripcion_proveedor = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    dividir = models.BooleanField(default=False)
    descuento = models.ForeignKey('precios.Descuento', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('proveedor', 'codigo_proveedor')
        indexes = [
            models.Index(fields=['proveedor', 'codigo_proveedor'])
        ]
        constraints = [
            models.CheckConstraint(
                name='one_relation_required',
                check=(
                    (models.Q(articulo__isnull=False) & models.Q(articulo_s_revisar__isnull=True)) |
                    (models.Q(articulo__isnull=True) & models.Q(articulo_s_revisar__isnull=False))
                )
            ),
            models.UniqueConstraint(fields=['precio_de_lista'], name='unique_ap_per_precio_de_lista')
        ]

    def save(self, *args, **kwargs):
        codigo_base = self.codigo_proveedor.rstrip('/')
        try:
            codigo_base = str(int(codigo_base.lstrip('0')))
        except ValueError:
            pass
        self.codigo_proveedor = f"{codigo_base}/"
        super().save(*args, **kwargs)

    def get_codigo_completo(self):
        return f"{self.codigo_proveedor.rstrip('/')}/{self.proveedor.abreviatura}"

    def generar_precios(self, cantidad=1, pago_efectivo=False):
        # Usar el descuento y proveedor del propio AP, independientemente del Articulo vinculado
        target = self.articulo if self.articulo else self.articulo_s_revisar
        if not target:
            return {'error': 'No hay artículo asociado'}
        # Priorizar descuento propio del AP; si no, usar el del target
        config_desc = self.descuento if getattr(self, 'descuento', None) else target.get_descuento()
        return target.generar_precios(
            precio_de_lista=self.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=self.dividir,
            bulto=self.precio_de_lista.bulto,
            iva=self.precio_de_lista.iva,
            descuento_override=config_desc,
            proveedor_override=self.proveedor,
        )
# Archivo de modelos del adaptador