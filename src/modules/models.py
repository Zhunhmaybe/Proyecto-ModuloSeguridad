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


    funciones = models.ManyToManyField(

        Funcion,

        through='FuncionModulo',

        related_name='modulos'

    )


    class Meta:

        db_table = 'modulos'


    def __str__(self):

        return self.nombre_modulo

class FuncionModulo(models.Model):

    id = models.AutoField(
        primary_key=True
    )


    funcion = models.ForeignKey(

        Funcion,

        on_delete=models.CASCADE,

        db_column='funcion_id'

    )


    modulo = models.ForeignKey(

        'Modulo',

        on_delete=models.CASCADE,

        db_column='modulo_id'

    )


    class Meta:

        db_table = 'funciones_modulos'
