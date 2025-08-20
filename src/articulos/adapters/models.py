from django.db import models
from django.apps import apps
from decimal import Decimal


class ArticuloBase(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    class Meta:
        abstract = True

    def generar_precios(self, precio_de_lista, cantidad=1, pago_efectivo=False, dividir=False, bulto=1, iva=0, descuento_override=None, proveedor_override=None):
        """Genera precios dinámicos.
        Permite overrides explícitos de descuento y proveedor para casos como ArticuloProveedor.
        """
        config = descuento_override if descuento_override is not None else self.get_descuento()
        proveedor = proveedor_override if proveedor_override is not None else self.get_proveedor()

        # Precio base para presupuestos
        if dividir and bulto > 0:
            base = precio_de_lista / bulto * (Decimal('1') + iva) * (Decimal('1') - proveedor.descuento_comercial)
        else:
            base = precio_de_lista * (Decimal('1') + iva) * (Decimal('1') - proveedor.descuento_comercial)

        # Precios calculados
        precio_final = base * proveedor.margen_ganancia
        precio_final_efectivo = precio_final * proveedor.margen_ganancia_efectivo

        # Monto por bulto (sin descuento por bulto aplicado aún)
        precio_bulto = precio_final * (bulto or 1)

        # Reglas para descuento por bulto
        # - Si cantidad != 1 => usar esa cantidad para evaluar el descuento
        # - Si cantidad == 1 => usar el bulto del artículo si > 1; de lo contrario, usar la cantidad definida en el descuento
        # - Si la política del descuento tiene cantidad_bulto <= 1, pero el artículo tiene bulto > 1,
        #   se toma el bulto del artículo como umbral (min_qty) para habilitar el descuento por bulto
        bulto_articulo = bulto or 1
        descuento_cant_bulto = getattr(config, 'cantidad_bulto', 1) or 1
        if cantidad != 1:
            applied_qty = cantidad
            min_qty = max(descuento_cant_bulto, 2)  # asegurar umbral > 1 para activar lógica de bulto
        else:
            applied_qty = bulto_articulo if bulto_articulo > 1 else descuento_cant_bulto
            # Si la política no define umbral (>1), usar el bulto del artículo como umbral si es >1
            min_qty = bulto_articulo if (descuento_cant_bulto <= 1 and bulto_articulo > 1) else descuento_cant_bulto
        descuento_bulto = getattr(config, 'bulto', 0)
        # Normalizar/validar descuento por bulto:
        # - Si viene como fracción (0<d<1), usarlo directo
        # - Si viene como porcentaje (1<d<=100), dividir por 100
        # - Si viene como factor multiplicativo (p.ej 0.9), lo convertimos a descuento: 1-0.9=0.1 más abajo
        try:
            descuento_bulto = Decimal(str(descuento_bulto))
        except Exception:
            descuento_bulto = Decimal('0')
        if descuento_bulto > Decimal('1') and descuento_bulto <= Decimal('100'):
            descuento_bulto = descuento_bulto / Decimal('100')
        elif descuento_bulto <= Decimal('0'):
            descuento_bulto = Decimal('0')
        elif descuento_bulto == Decimal('1'):
            descuento_bulto = Decimal('0')
        # El factor multiplicativo que aplica al precio por bulto luego del descuento
        factor_descuento_bulto = Decimal('1') - descuento_bulto

        apply_bulk_discount = (
            getattr(config, 'is_active', lambda: True)() and
            min_qty > 1 and
            applied_qty >= min_qty and
            (Decimal('0') < descuento_bulto < Decimal('1'))
        )
        precio_final_bulto = precio_bulto * (factor_descuento_bulto if apply_bulk_discount else Decimal('1'))
        precio_final_bulto_efectivo = precio_final_bulto * proveedor.margen_ganancia_efectivo

        # Aplicar descuento general si es temporal y activo
        if getattr(config, 'is_active', lambda: True)() and getattr(config, 'general', 0) > 0:
            g = (Decimal('1') - Decimal(str(config.general)))
            precio_final *= g
            precio_final_efectivo *= g
            precio_final_bulto *= g
            precio_final_bulto_efectivo *= g

        return {
            'base': round(base, 2),
            'final': round(precio_final, 2),
            'final_efectivo': round(precio_final_efectivo, 2),
            'bulto': round(precio_bulto, 2),
            'final_bulto': round(precio_final_bulto, 2),
            'final_bulto_efectivo': round(precio_final_bulto_efectivo, 2),
            'cantidad_bulto_aplicada': int(applied_qty),
            # Debug fields
            'debug_descuento_bulto': float(descuento_bulto),
            'debug_cantidad_bulto_politica': int(descuento_cant_bulto),
            'debug_bulto_articulo': int(bulto_articulo),
            'debug_min_qty': int(min_qty),
            'debug_applied_qty': int(applied_qty),
            'debug_aplica_descuento_bulto': bool(apply_bulk_discount),
            'debug_factor_descuento_bulto': float(factor_descuento_bulto),
        }

    def get_descuento(self):
        raise NotImplementedError

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
        ap = self.articuloproveedor_set.first()
        Descuento = apps.get_model('precios', 'Descuento')
        return ap.descuento if ap and ap.descuento and ap.descuento.is_active() else Descuento.objects.get(tipo="Sin Descuento")

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
    descuento = models.ForeignKey('precios.Descuento', on_delete=models.SET_NULL, null=True, blank=True)

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
        if not self.descuento:
            Descuento = apps.get_model('precios', 'Descuento')
            self.descuento = Descuento.objects.get(tipo="Sin Descuento")
        super().save(*args, **kwargs)

    def get_descuento(self):
        Descuento = apps.get_model('precios', 'Descuento')
        return self.descuento if self.descuento and self.descuento.is_active() else Descuento.objects.get(tipo="Sin Descuento")

    def get_proveedor(self):
        return self.proveedor

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
        if not self.descuento:
            Descuento = apps.get_model('precios', 'Descuento')
            self.descuento = Descuento.objects.get(tipo="Sin Descuento")
        super().save(*args, **kwargs)

    def get_codigo_completo(self):
        return f"{self.codigo_proveedor.rstrip('/')}/{self.proveedor.abreviatura}"

    def generar_precios(self, cantidad=1, pago_efectivo=False):
        # Usar el descuento y proveedor del propio AP, independientemente del Articulo vinculado
        target = self.articulo if self.articulo else self.articulo_s_revisar
        if not target:
            return {'error': 'No hay artículo asociado'}
        # Si no hay descuento asignado, usar "Sin Descuento"
        Descuento = apps.get_model('precios', 'Descuento')
        config_desc = self.descuento if (self.descuento and self.descuento.is_active()) else Descuento.objects.get(tipo="Sin Descuento")
        return target.generar_precios(
            precio_de_lista=self.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=self.dividir if self.articulo else False,
            bulto=self.precio_de_lista.bulto,
            iva=self.precio_de_lista.iva if self.articulo else 0,
            descuento_override=config_desc,
            proveedor_override=self.proveedor,
        )
# Archivo de modelos del adaptador