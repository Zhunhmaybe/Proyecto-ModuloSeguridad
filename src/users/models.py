from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, user_name, email, cedula, password=None, **extra_fields):
        if not user_name:
            raise ValueError('El usuario debe tener un user_name')
        if not email:
            raise ValueError('El usuario debe tener un email')
        
        email = self.normalize_email(email)
        user = self.model(user_name=user_name, email=email, cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, email, cedula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('estado', True)
        return self.create_user(user_name, email, cedula, password, **extra_fields)

#Tockens para recuperar contraseña
class PasswordResetToken(models.Model):

    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )

    usado = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'password_reset_tokens'

class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=100)
    estado_rol = models.BooleanField(default=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre_rol

class Usuario(AbstractBaseUser, PermissionsMixin):
    user_name = models.CharField(max_length=16, unique=True)
    cedula = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'
    
    # Required for Django admin
    is_staff = models.BooleanField(default=False)
    
    # Relación muchos a muchos con Roles
    roles = models.ManyToManyField(Rol, related_name='usuarios', blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'user_name'
    REQUIRED_FIELDS = ['email', 'cedula']

    def __str__(self):
        return self.user_name

    @property
    def is_active(self):
        return self.estado
