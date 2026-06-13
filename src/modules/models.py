from django.db import models
from users.models import Rol

class Modulo(models.Model):
    id_modulo = models.AutoField(primary_key=True)
    nombre_modulo = models.CharField(max_length=100)
    descripcion_modulo = models.TextField(blank=True, null=True)
    estado_modulo = models.BooleanField(default=True)

    class Meta:
        db_table = 'modulos'

    def __str__(self):
        return self.nombre_modulo

class Funcion(models.Model):
    id_funcion = models.AutoField(primary_key=True)
    nombre_funcion = models.CharField(max_length=100)
    estado_funcion = models.BooleanField(default=True)

    class Meta:
        db_table = 'funciones'
    
    # Un módulo puede tener múltiples funciones, y una función puede pertenecer a varios módulos (según ER)
    # Aunque a menudo una función pertenece a un solo módulo. El ER muestra modulos_funciones como M2M.
    modulos = models.ManyToManyField(Modulo, related_name='funciones', blank=True)
    
    # Relación M2M con Roles (roles_funciones)
    roles = models.ManyToManyField(Rol, related_name='funciones', blank=True)

    def __str__(self):
        return self.nombre_funcion
