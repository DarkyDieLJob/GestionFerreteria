from django.db import models
from django.utils import timezone

class PrecioDeLista(models.Model):
    codigo = models.CharField(max_length=50)  # e.g., '37/', '0037-25/'
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    iva = models.DecimalField(max_digits=5, decimal_places=2, default=0.21)
    bulto = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('proveedor', 'codigo')
        indexes = [
            models.Index(fields=['codigo'])
        ]

    def save(self, *args, **kwargs):
        codigo_base = self.codigo.rstrip('/')
        try:
            codigo_base = str(int(codigo_base.lstrip('0')))
        except ValueError:
            pass
        self.codigo = f"{codigo_base}/"
        super().save(*args, **kwargs)

    def get_codigo_completo(self):
        return f"{self.codigo.rstrip('/')}/{self.proveedor.abreviatura}"
# Archivo de modelos del adaptador


class Descuento(models.Model):
    tipo = models.CharField(max_length=50, default="Sin Descuento")
    efectivo = models.DecimalField(max_digits=5, decimal_places=2, default=0.10)  # 10% descuento
    bulto = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)  # 5% descuento
    cantidad_bulto = models.PositiveIntegerField(default=5)
    general = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # 0% por defecto
    temporal = models.BooleanField(default=False)
    desde = models.DateTimeField(null=True, blank=True)
    hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['desde', 'hasta'])
        ]

    def save(self, *args, **kwargs):
        if self.temporal and (not self.desde or not self.hasta):
            raise ValueError("Descuentos temporales requieren desde y hasta")
        if self.temporal and self.hasta < self.desde:
            raise ValueError("Fecha hasta debe ser mayor a desde")
        super().save(*args, **kwargs)

    def is_active(self):
        if not self.temporal:
            return True
        now = timezone.now()
        # Tolerancia pequeña para evitar flaquezas por tiempo entre creación y evaluación
        # y la evaluación ocurre instantes después de la creación.
        upper_bound = self.hasta
        try:
            from datetime import timedelta
            upper_bound = self.hasta + timedelta(seconds=1)
        except Exception:
            pass
        return self.desde <= now <= upper_bound
