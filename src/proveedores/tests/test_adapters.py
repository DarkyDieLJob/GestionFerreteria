from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from proveedores.adapters.models import Proveedor, Contacto, ContactoProveedor


class ProveedoresModelsTest(TestCase):
    databases = {'default', 'negocio_db'}

    def test_proveedor_save_uppercases_abreviatura(self):
        p = Proveedor.objects.create(nombre="Proveedor X", abreviatura="px")
        self.assertEqual(p.abreviatura, "PX")

    def test_contacto_proveedor_relation(self):
        p = Proveedor.objects.create(nombre="Prov A", abreviatura="pa")
        c = Contacto.objects.create(nombre="Ana", apellido="Perez", email="ana@example.com", telefono="123")
        link = ContactoProveedor.objects.create(proveedor=p, contacto=c)
        self.assertEqual(link.proveedor, p)
        self.assertEqual(link.contacto, c)
# Pruebas para los adaptadores

    def test_proveedor_abreviatura_unique_case_insensitive(self):
        Proveedor.objects.create(nombre="Prov1", abreviatura="px")  # se guarda como PX
        with self.assertRaises(IntegrityError):
            Proveedor.objects.create(nombre="Prov2", abreviatura="PX")

    def test_contacto_email_validation(self):
        c = Contacto(nombre="Juan", apellido="Lopez", email="no-es-email", telefono="555")
        with self.assertRaises(ValidationError):
            c.full_clean()  # EmailField valida en full_clean

    def test_cascade_delete_proveedor_elimina_contacto_proveedor(self):
        p = Proveedor.objects.create(nombre="Prov B", abreviatura="pb")
        c = Contacto.objects.create(nombre="Beto", apellido="Diaz", email="beto@example.com", telefono="321")
        ContactoProveedor.objects.create(proveedor=p, contacto=c)
        p.delete()
        self.assertEqual(ContactoProveedor.objects.count(), 0)

    def test_cascade_delete_contacto_elimina_contacto_proveedor(self):
        p = Proveedor.objects.create(nombre="Prov C", abreviatura="pc")
        c = Contacto.objects.create(nombre="Caro", apellido="Suarez", email="caro@example.com", telefono="999")
        ContactoProveedor.objects.create(proveedor=p, contacto=c)
        c.delete()
        self.assertEqual(ContactoProveedor.objects.count(), 0)

    def test_proveedor_defaults_desc_margenes(self):
        p = Proveedor.objects.create(nombre="Prov D", abreviatura="pd")
        # defaults definidos en modelo
        self.assertIsNotNone(p.descuento_comercial)
        self.assertIsNotNone(p.margen_ganancia)
        self.assertIsNotNone(p.margen_ganancia_efectivo)
        self.assertIsNotNone(p.margen_ganancia_bulto)