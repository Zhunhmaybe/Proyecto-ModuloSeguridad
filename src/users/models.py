from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

def validate_email_domain(value):
    if not value.endswith('@utn.edu.ec') and not value.endswith('@gmail.com'):
        raise ValidationError('El correo debe terminar en @utn.edu.ec o @gmail.com')

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

class EmailVerificationToken(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verification_tokens'

class Rol(models.Model):

    id_rol = models.AutoField(primary_key=True)

    nombre_rol = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False
    )

    estado_rol = models.BooleanField(
        default=True
    )


    funciones = models.ManyToManyField(
        'Funcion',
        through='FuncionRol',
        related_name='roles'
    )


    class Meta:
        db_table = 'roles'


    def __str__(self):
        return self.nombre_rol

class Usuario(AbstractBaseUser, PermissionsMixin):
    user_name = models.CharField(
        max_length=16, 
        unique=True,
        null=False,
        blank=False,
        validators=[MinLengthValidator(8, message="El usuario debe tener mínimo 8 caracteres.")]
    )
    cedula = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True, null=False, blank=False, validators=[validate_email_domain])
    correo_verificado = models.BooleanField(default=False)
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
    
class Funcion(models.Model):

    id_funcion = models.AutoField(primary_key=True)


    nombre_funcion = models.CharField(
        max_length=100,
        unique=True
    )


    estado_funcion = models.BooleanField(
        default=True
    )


    class Meta:
        db_table = 'funciones'


    def __str__(self):
        return self.nombre_funcion
    
class FuncionRol(models.Model):

    id = models.AutoField(
        primary_key=True
    )


    funcion = models.ForeignKey(

        Funcion,

        on_delete=models.CASCADE,

        db_column='funcion_id'

    )


    rol = models.ForeignKey(

        Rol,

        on_delete=models.CASCADE,

        db_column='rol_id'

    )
    class Meta:

        db_table = 'funciones_roles'
