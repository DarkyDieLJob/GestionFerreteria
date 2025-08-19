from django.db import models

# Archivo de modelos del adaptador
class ConfigImportacion(models.Model):
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    nombre_config = models.CharField(max_length=100, default='default')
    col_codigo = models.CharField(max_length=10, blank=True, null=True)
    col_descripcion = models.CharField(max_length=10, blank=True, null=True)
    col_precio = models.CharField(max_length=10, blank=True, null=True)
    col_cant = models.CharField(max_length=10, blank=True, null=True)
    col_iva = models.CharField(max_length=10, blank=True, null=True)
    col_cod_barras = models.CharField(max_length=10, blank=True, null=True)
    col_marca = models.CharField(max_length=10, blank=True, null=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    instructivo = models.TextField(blank=True)

    class Meta:
        unique_together = ('proveedor', 'nombre_config')


class ArchivoPendiente(models.Model):
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    ruta_csv = models.CharField(max_length=255)
    hoja_origen = models.CharField(max_length=255)
    config_usada = models.ForeignKey('importaciones.ConfigImportacion', on_delete=models.PROTECT)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)
