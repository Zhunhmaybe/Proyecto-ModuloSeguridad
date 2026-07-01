from django.db import models
from users.models import Rol
from users.models import Funcion

class Modulo(models.Model):

    id_modulo = models.AutoField(
        primary_key=True
    )


    nombre_modulo = models.CharField(
        max_length=100
    )


    descripcion_modulo = models.CharField(
        max_length=255
    )


    estado_modulo = models.BooleanField(
        default=True
    )


    class Meta:

        db_table = 'modulos'


    def __str__(self):

        return self.nombre_modulo

