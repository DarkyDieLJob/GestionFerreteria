from django.test import TestCase

from proveedores.adapters.models import Proveedor, Contacto, ContactoProveedor


class ProveedoresSmokeTest(TestCase):
    databases = {'default', 'negocio_db'}

    def test_abreviatura_guardada_en_mayusculas(self):
        p = Proveedor.objects.create(nombre="Proveedor Z", abreviatura="zz")
        self.assertEqual(p.abreviatura, "ZZ")

    def test_contacto_proveedor_relacion(self):
        p = Proveedor.objects.create(nombre="Proveedor Y", abreviatura="py")
        c = Contacto.objects.create(nombre="N", apellido="A", email="n@example.com", telefono="1")
        cp = ContactoProveedor.objects.create(proveedor=p, contacto=c)
        self.assertEqual(cp.proveedor, p)
        self.assertEqual(cp.contacto, c)
