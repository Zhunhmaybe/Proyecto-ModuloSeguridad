"""
Tests para la app 'audit'.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from audit.models import Auditoria
from users.models import Funcion

Usuario = get_user_model()

# Cédulas ecuatorianas válidas para tests
CEDULAS = [
    '1700000001', '1700000019', '1700000027',
]


class AuditoriaModelTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            user_name="audituser",
            email="audituser@gmail.com",
            cedula=CEDULAS[0],
            password="Clave@123"
        )
        self.funcion = Funcion.objects.create(nombre_funcion="GESTIONAR_LOGS")

    def test_crear_auditoria_sin_funcion(self):
        a = Auditoria.objects.create(
            username=self.user,
            accion="LOGIN EXITOSO",
            descripcion="Usuario inició sesión correctamente",
            estado_auditoria=True
        )
        self.assertEqual(a.accion, "LOGIN EXITOSO")
        self.assertTrue(a.estado_auditoria)
        self.assertIsNone(a.id_funciones)

    def test_crear_auditoria_con_funcion(self):
        a = Auditoria.objects.create(
            username=self.user,
            id_funciones=self.funcion,
            accion="CREAR_ROL",
            descripcion="Se creó el rol ADMIN",
            estado_auditoria=True
        )
        self.assertEqual(a.id_funciones, self.funcion)

    def test_auditoria_str(self):
        a = Auditoria.objects.create(
            username=self.user,
            accion="LOGOUT",
            estado_auditoria=True
        )
        self.assertIn("LOGOUT", str(a))

    def test_auditoria_tabla_correcta(self):
        self.assertEqual(Auditoria._meta.db_table, "auditoria")

    def test_auditoria_fallo_login(self):
        a = Auditoria.objects.create(
            username=self.user,
            accion="LOGIN FALLIDO",
            descripcion="Credenciales incorrectas",
            estado_auditoria=False
        )
        self.assertFalse(a.estado_auditoria)

    def test_auditoria_usuario_null_al_borrar_usuario(self):
        """Al eliminar un usuario, la FK queda NULL (SET_NULL)."""
        user_tmp = Usuario.objects.create_user(
            user_name="tmp_del",
            email="tmpdel@gmail.com",
            cedula=CEDULAS[1],
            password="Clave@123"
        )
        a = Auditoria.objects.create(
            username=user_tmp,
            accion="ACCION_TEST",
            estado_auditoria=True
        )
        user_tmp.delete()
        a.refresh_from_db()
        self.assertIsNone(a.username)

    def test_auditoria_observacion_nullable(self):
        a = Auditoria.objects.create(
            username=self.user,
            accion="ACCION_SIN_OBS",
            estado_auditoria=True
        )
        self.assertIsNone(a.observacion)
