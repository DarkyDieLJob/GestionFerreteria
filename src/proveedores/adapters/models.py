from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    abreviatura = models.CharField(max_length=10, unique=True)
    descuento_comercial = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # e.g., 0.1 (10%)
    margen_ganancia = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)  # 50% margen
    margen_ganancia_efectivo = models.DecimalField(max_digits=5, decimal_places=2, default=0.90)  # 10% descuento efectivo
    margen_ganancia_bulto = models.DecimalField(max_digits=5, decimal_places=2, default=0.95)  # 5% descuento bulto

    class Meta:
        indexes = [
            models.Index(fields=['abreviatura'])
        ]

    def save(self, *args, **kwargs):
        self.abreviatura = self.abreviatura.upper()
        super().save(*args, **kwargs)
        
class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)# Archivo de modelos del adaptador


class ContactoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE)
