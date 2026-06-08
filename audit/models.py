from django.db import models
from users.models import Usuario
from modules.models import Funcion

class Auditoria(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    # Según el ER, username es FK a Usuario.
    username = models.ForeignKey(Usuario, to_field='user_name', on_delete=models.SET_NULL, null=True, db_column='username')
    id_funciones = models.ForeignKey(Funcion, on_delete=models.SET_NULL, null=True, db_column='id_funciones')
    accion = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    estado_auditoria = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} por {self.username}"
