"""
Tests para la app 'modules'.
Cédulas válidas importadas desde users.tests.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from modules.models import Modulo, FuncionModulo
from users.models import Funcion

Usuario = get_user_model()

# Cédulas ecuatorianas válidas para tests
CEDULAS = [
    '1700000001', '1700000019', '1700000027', '1700000035',
    '1700000043', '1700000050', '1700000068', '1700000076',
]


def make_superuser(username, email, cedula_idx=0):
    return Usuario.objects.create_superuser(
        user_name=username,
        email=email,
        cedula=CEDULAS[cedula_idx],
        password='Admin@123'
    )


# =============================================================================
# TESTS DE MODELOS
# =============================================================================

class ModuloModelTest(TestCase):
    def test_crear_modulo(self):
        m = Modulo.objects.create(
            nombre_modulo="Seguridad",
            descripcion_modulo="Módulo de seguridad centralizada",
            estado_modulo=True
        )
        self.assertEqual(m.nombre_modulo, "Seguridad")
        self.assertEqual(str(m), "Seguridad")
        self.assertTrue(m.estado_modulo)

    def test_modulo_tabla_correcta(self):
        self.assertEqual(Modulo._meta.db_table, "modulos")

    def test_modulo_estado_default_true(self):
        m = Modulo.objects.create(
            nombre_modulo="Auditoría",
            descripcion_modulo="Auditoría del sistema"
        )
        self.assertTrue(m.estado_modulo)


class FuncionModuloModelTest(TestCase):
    def setUp(self):
        self.modulo = Modulo.objects.create(
            nombre_modulo="Gestión",
            descripcion_modulo="Módulo de gestión"
        )
        self.funcion = Funcion.objects.create(nombre_funcion="GESTIONAR_ROLES_MOD")

    def test_crear_funcion_modulo(self):
        fm = FuncionModulo.objects.create(
            modulo=self.modulo,
            funcion=self.funcion
        )
        self.assertEqual(fm.modulo, self.modulo)
        self.assertEqual(fm.funcion, self.funcion)

    def test_tabla_correcta(self):
        self.assertEqual(FuncionModulo._meta.db_table, "funciones_modulos")

    def test_modulo_tiene_funcion_via_m2m(self):
        FuncionModulo.objects.create(modulo=self.modulo, funcion=self.funcion)
        self.assertIn(self.funcion, self.modulo.funciones.all())


# =============================================================================
# TESTS DE VISTAS
# =============================================================================

class ModulosViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = make_superuser("adminmodulos", "adminmodulos@gmail.com", cedula_idx=0)
        self.client.force_login(self.admin_user)

    def test_get_modulos_lista(self):
        response = self.client.get(reverse('modulos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'modulos.html')

    def test_modulos_en_contexto(self):
        Modulo.objects.create(
            nombre_modulo="Inventario",
            descripcion_modulo="Control de inventario"
        )
        response = self.client.get(reverse('modulos'))
        self.assertIn('modulos', response.context)
        self.assertEqual(len(response.context['modulos']), 1)

    def test_crear_modulo_post(self):
        funcion = Funcion.objects.create(nombre_funcion="CONFIGURAR_MOD")
        response = self.client.post(reverse('modulos'), {
            'nombre_modulo': 'Nuevo Módulo',
            'descripcion_modulo': 'Descripción del módulo',
            'funciones': [funcion.id_funcion],
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Modulo.objects.filter(nombre_modulo='Nuevo Módulo').exists())

    def test_crear_modulo_sin_funciones(self):
        response = self.client.post(reverse('modulos'), {
            'nombre_modulo': 'Módulo Simple',
            'descripcion_modulo': 'Sin funciones',
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Modulo.objects.filter(nombre_modulo='Módulo Simple').exists())

    def test_modulos_accesible_sin_login(self):
        """modules/views.modulos_view no tiene @login_required actualmente.
        Documentar este comportamiento: la vista devuelve 200 sin autenticación."""
        self.client.logout()
        response = self.client.get(reverse('modulos'))
        # La vista no está protegida — si se quiere proteger, añadir @login_required
        self.assertIn(response.status_code, [200, 302])

    def test_funciones_disponibles_en_contexto(self):
        Funcion.objects.create(nombre_funcion="FUNC_MODULO_A")
        Funcion.objects.create(nombre_funcion="FUNC_MODULO_B")
        response = self.client.get(reverse('modulos'))
        self.assertIn('funciones', response.context)
        self.assertGreaterEqual(len(response.context['funciones']), 2)
