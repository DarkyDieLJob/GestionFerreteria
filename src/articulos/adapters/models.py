from django.db import models
from django.apps import apps


class ArticuloBase(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    class Meta:
        abstract = True

    def generar_precios(self, precio_de_lista, cantidad=1, pago_efectivo=False, dividir=False, bulto=1, iva=0):
        """Genera precios dinámicos."""
        config = self.get_descuento()
        proveedor = self.get_proveedor()

        # Precio base para presupuestos
        if dividir and bulto > 0:
            base = precio_de_lista / bulto * (1 + iva) * (1 - proveedor.descuento_comercial)
        else:
            base = precio_de_lista * (1 + iva) * (1 - proveedor.descuento_comercial)

        # Precios calculados
        precio_final = base * proveedor.margen_ganancia
        precio_final_efectivo = precio_final * proveedor.margen_ganancia_efectivo
        precio_bulto = precio_final * bulto
        precio_final_bulto = precio_bulto * config.bulto if cantidad >= config.cantidad_bulto else precio_bulto
        precio_final_bulto_efectivo = precio_final_bulto * proveedor.margen_ganancia_efectivo

        # Aplicar descuento general si es temporal y activo
        if config.is_active() and config.general > 0:
            precio_final *= (1 - config.general)
            precio_final_efectivo *= (1 - config.general)
            precio_final_bulto *= (1 - config.general)
            precio_final_bulto_efectivo *= (1 - config.general)

        return {
            'base': round(base, 2),
            'final': round(precio_final, 2),
            'final_efectivo': round(precio_final_efectivo, 2),
            'bulto': round(precio_bulto, 2),
            'final_bulto': round(precio_final_bulto, 2),
            'final_bulto_efectivo': round(precio_final_bulto_efectivo, 2)
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

    def generar_precios(self, cantidad=1, pago_efectivo=False):
        return super().generar_precios(
            precio_de_lista=self.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=False,  # ArticuloSinRevisar no usa dividir
            bulto=1,
            iva=0
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
            )
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
        return super(Articulo, self.articulo).generar_precios(
            precio_de_lista=self.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=self.dividir,
            bulto=self.precio_de_lista.bulto,
            iva=self.precio_de_lista.iva
        ) if self.articulo else super(ArticuloSinRevisar, self.articulo_s_revisar).generar_precios(
            precio_de_lista=self.precio,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
            dividir=False,
            bulto=1,
            iva=0
        )
# Archivo de modelos del adaptador