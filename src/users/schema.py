# pyrefly: ignore [missing-import]
import strawberry
from dataclasses import dataclass
from typing import List, Optional
from users.models import Usuario, Rol
from audit.models import Auditoria
from modules.models import Modulo, Funcion
import os
# pyrefly: ignore [missing-import]
import msal
# pyrefly: ignore [missing-import]
import jwt
import datetime
# pyrefly: ignore [missing-import]
from django.core.mail import send_mail
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from django.urls import reverse

# --- JWT Config ---
JWT_SECRET = os.getenv('SECRET_KEY', 'secret')

def generate_jwt(user):
    roles = list(user.roles.filter(estado_rol=True).values_list('nombre_rol', flat=True))
    funciones = list(Funcion.objects.filter(roles__usuarios=user, estado_funcion=True).values_list('nombre_funcion', flat=True).distinct())
    
    payload = {
        'user_id': user.id,
        'user_name': user.user_name,
        'email': user.email,
        'roles': roles,
        'permissions': funciones,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30) # Token válido por 30 minutos
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# --- MSAL Config ---
def validate_microsoft_token(username, password):
    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID")
    
    if not client_id or client_id == "tu-client-id":
        # MODO DE PRUEBA: Si no se configuran las credenciales, simula que Microsoft aprueba si el password es "123"
        if password == "123":
            return True, "Mock_Token_Prueba"
        return False, "Credenciales inválidas"

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret
    )
    
    # Flujo ROPC (Resource Owner Password Credential)
    result = app.acquire_token_by_username_password(
        username=username,
        password=password,
        scopes=["User.Read"]
    )
    
    if "access_token" in result:
        return True, result["access_token"]
    else:
        return False, result.get("error_description", "Error de autenticación con Microsoft")

@strawberry.type
@dataclass
class FuncionType:
    id_funcion: int
    nombre_funcion: str
    estado_funcion: bool

@strawberry.type
@dataclass
class RolType:
    id_rol: int
    nombre_rol: str
    estado_rol: bool
    funciones: List[FuncionType]

@strawberry.type
@dataclass
class UsuarioType:
    id: int
    user_name: str
    email: str
    cedula: str
    estado: bool
    roles: List[RolType]

def map_user_to_type(u: Usuario) -> UsuarioType:
    roles_list = []
    for r in u.roles.all():
        func_list = []
        for f in r.funciones.all():
            func_list.append(FuncionType(
                id_funcion=f.id_funcion,
                nombre_funcion=f.nombre_funcion,
                estado_funcion=f.estado_funcion
            ))
        roles_list.append(RolType(
            id_rol=r.id_rol,
            nombre_rol=r.nombre_rol,
            estado_rol=r.estado_rol,
            funciones=func_list
        ))
    return UsuarioType(
        id=u.id,
        user_name=u.user_name,
        email=u.email,
        cedula=u.cedula,
        estado=u.estado,
        roles=roles_list
    )

@strawberry.type
@dataclass
class LoginResponse:
    success: bool
    token: Optional[str]
    message: Optional[str]
    # actions: List[str] # Lista de permisos para HU7 (Opcional, se puede ampliar)
    
#Registrar Usuario
@strawberry.type
@dataclass
class RegisterResponse:
    success: bool
    message: str
#Recuperar Contraseña
@strawberry.type
@dataclass
class ForgotPasswordResponse:
    success: bool
    message: str

@strawberry.type
@dataclass
class ResetPasswordResponse:
    success: bool
    message: str

@strawberry.type
@dataclass
class AuditResponse:
    success: bool
    message: str

@strawberry.type
@dataclass
class ListadoFuncionesResponse:
    success: bool
    message: Optional[str]
    funciones: Optional[List[str]]

@strawberry.type
class Query:
    @strawberry.field
    def usuarios(self) -> List[UsuarioType]:
        # Convierte los modelos ORM a tipos de Strawberry
        users = Usuario.objects.all()
        return [map_user_to_type(u) for u in users]

    @strawberry.field
    def me(self, info: strawberry.Info) -> Optional[UsuarioType]:
        request = info.context.get("request")
        if not request:
            return None
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user_id = payload.get("user_id")
            u = Usuario.objects.get(id=user_id)
            if not u.estado:
                return None
            return map_user_to_type(u)
        except (jwt.PyJWTError, Usuario.DoesNotExist):
            return None

    @strawberry.field
    def user_functions(self, token: str, modulo_id: int) -> ListadoFuncionesResponse:
        user = None
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user_id = payload.get("user_id")
            user = Usuario.objects.get(id=user_id)
            if not user.estado:
                raise Exception("Usuario inactivo")
        except Exception as e:
            Auditoria.objects.create(
                accion="CONSULTA FUNCIONES FALLIDA",
                descripcion="Token invalido",
                estado_auditoria=False
            )
            return ListadoFuncionesResponse(success=False, message="Token invalido", funciones=None)

        try:
            modulo = Modulo.objects.get(id_modulo=modulo_id)
            if not modulo.estado_modulo:
                raise Exception("Modulo inactivo")
        except Exception as e:
            Auditoria.objects.create(
                username=user,
                accion="CONSULTA FUNCIONES FALLIDA",
                descripcion="Modulo invalido",
                estado_auditoria=False
            )
            return ListadoFuncionesResponse(success=False, message="Modulo invalido", funciones=None)

        funciones_usuario = Funcion.objects.filter(
            roles__usuarios=user,
            estado_funcion=True,
            modulos=modulo
        ).values_list('nombre_funcion', flat=True).distinct()

        return ListadoFuncionesResponse(
            success=True,
            message="Exito",
            funciones=list(funciones_usuario)
        )

@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, username: str, password: str, modulo_id: Optional[int] = None) -> LoginResponse:
        try:
            # 1. Validar usuario en DB
            user = Usuario.objects.get(user_name=username)
            if not user.estado:
                return LoginResponse(success=False, token=None, message="Usuario inactivo")
            
            # Validar módulo si se envía (HU7)
            if modulo_id:
                try:
                    modulo = Modulo.objects.get(id_modulo=modulo_id)
                    if not modulo.estado_modulo:
                        return LoginResponse(success=False, token=None, message="Módulo inactivo")
                except Modulo.DoesNotExist:
                    return LoginResponse(success=False, token=None, message="Módulo no existe")

            # 2. Validar contraseña localmente o con Microsoft Entra ID (MSAL)
            if user.check_password(password):
                is_valid = True
                ms_result = "Autenticación Local"
            else:
                is_valid, ms_result = validate_microsoft_token(username, password)
                
            if not is_valid:
                # HU8: CA2 - Guardar pista de auditoría en intento fallido
                Auditoria.objects.create(
                    username=user,
                    accion="LOGIN FALLIDO",
                    descripcion=f"Intento fallido: {ms_result}",
                    estado_auditoria=False
                )
                return LoginResponse(success=False, token=None, message=f"Credenciales inválidas: {ms_result}")
            
            # 3. Generar JWT propio para los demás módulos
            token = generate_jwt(user)
            
            # HU8: CA4 - Guardar pista de auditoría de éxito
            Auditoria.objects.create(
                username=user,
                accion="LOGIN EXITOSO",
                descripcion="Autenticación con MS exitosa",
                estado_auditoria=True
            )
            
            return LoginResponse(success=True, token=token, message="Inicio de sesión exitoso")

        except Usuario.DoesNotExist:
            return LoginResponse(success=False, token=None, message="Usuario no existe en Seguridades")

    @strawberry.mutation
    def register_user(
        self,
        info: strawberry.Info,
        username:str,
        email:str,
        cedula:str,
        password:str,
        confirm_password:str
    )-> RegisterResponse:
        # pyrefly: ignore [missing-import]
        import re
        # pyrefly: ignore [missing-import]
        from django.db import IntegrityError

        if Usuario.objects.filter(user_name=username).exists():
            return RegisterResponse(success=False, message="El usuario ya existe")

        if Usuario.objects.filter(email=email).exists():
            return RegisterResponse(success=False, message="El correo ya está registrado")
            
        if not re.match(r'^[a-zA-Z0-9._%+-]+@(gmail\.com|utn\.edu\.ec)$', email):
            return RegisterResponse(success=False, message="Solo se permiten correos @gmail.com o @utn.edu.ec")

        # Validar cédula: solo números y longitud exacta de 10 caracteres (máximo 10)
        if not cedula.isdigit():
            return RegisterResponse(success=False, message="La cédula debe contener solo números")
        if len(cedula) != 10:
            return RegisterResponse(success=False, message="La cédula debe tener exactamente 10 dígitos")

        if password != confirm_password:
            return RegisterResponse(success=False, message="Las contraseñas no coinciden")

        # Validar contraseña: al menos 8 caracteres, 1 mayúscula, 1 minúscula, 1 especial
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[@$!%*?&\.\-\_])[A-Za-z\d@$!%*?&\.\-\_]{8,}$', password):
            return RegisterResponse(success=False, message="La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un carácter especial (@$!%*?&.-_)")

        try:
            user = Usuario.objects.create_user(
                user_name=username,
                email=email,
                cedula=cedula,
                password=password
            )
            
            from users.models import EmailVerificationToken
        
            # pyrefly: ignore [missing-import]
            from django.core.mail import send_mail
            # pyrefly: ignore [missing-import]
            from django.conf import settings
            
            token = EmailVerificationToken.objects.create(usuario=user)
            request = info.context.get("request")
            if request:
                verify_url = request.build_absolute_uri(f'/verify-email/{token.token}/')
            else:
                verify_url = f"http://localhost:8000/verify-email/{token.token}/"

            try:
                send_mail(
                    subject='Bienvenido - Verifica tu correo',
                    message=f'Hola {user.user_name},\n\nGracias por registrarte en Seguridad Centralizada. Por favor verifica tu correo electrónico haciendo clic en el siguiente enlace:\n{verify_url}',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception:
                pass # Si el correo falla, de todas formas retornamos éxito pero sin bloquear
                
            return RegisterResponse(success=True, message="Usuario registrado correctamente. Revisa tu correo para verificar tu cuenta.")
        except IntegrityError as e:
            error_msg = str(e).lower()
            if 'cedula_valida' in error_msg:
                return RegisterResponse(success=False, message="La cédula ingresada no es válida en Ecuador")
            elif 'cedula' in error_msg:
                return RegisterResponse(success=False, message="La cédula ya se encuentra registrada")
            else:
                return RegisterResponse(success=False, message="Verifica tus datos")

    @strawberry.mutation
    def forgot_password(self, info: strawberry.Info, email: str) -> ForgotPasswordResponse:
        try:
            user = Usuario.objects.get(email=email)
            from users.models import PasswordResetToken, generar_codigo_6_digitos
            PasswordResetToken.objects.filter(usuario=user, usado=False).update(usado=True)
            token = PasswordResetToken.objects.create(usuario=user, codigo=generar_codigo_6_digitos())

            try:
                send_mail(
                    subject='Código de Recuperación - Seguridad Centralizada',
                    message=f'Hola {user.user_name},\n\nTu código de recuperación de 6 dígitos es:\n{token.codigo}\n\nIngresa este código en la aplicación para restablecer tu contraseña. Si no solicitaste esto, ignora este correo.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return ForgotPasswordResponse(success=True, message="Código enviado al correo.")
            except Exception as e:
                return ForgotPasswordResponse(success=False, message=f"Fallo al enviar correo: {str(e)}")

        except Usuario.DoesNotExist:
            return ForgotPasswordResponse(success=False, message="Correo no registrado")

    @strawberry.mutation
    def reset_password(self, email: str, codigo: str, password: str, confirm_password: str) -> ResetPasswordResponse:
        from users.models import PasswordResetToken
        try:
            codigo = codigo.upper().strip()
            user = Usuario.objects.get(email=email)
            reset_token = PasswordResetToken.objects.filter(usuario=user, codigo=codigo, usado=False).first()
            
            if not reset_token:
                return ResetPasswordResponse(success=False, message="Código inválido o expirado")
                
            if password != confirm_password:
                return ResetPasswordResponse(success=False, message="Las contraseñas no coinciden")
            if len(password) < 8:
                return ResetPasswordResponse(success=False, message="La contraseña debe tener al menos 8 caracteres")
                
            user.set_password(password)
            user.save()
            
            reset_token.usado = True
            reset_token.save()
            
            return ResetPasswordResponse(success=True, message="Contraseña actualizada exitosamente")
        except Usuario.DoesNotExist:
            return ResetPasswordResponse(success=False, message="Usuario no encontrado")

    @strawberry.mutation
    def create_audit_log(
        self,
        token: str,
        id_funcion: int,
        accion: str,
        descripcion: str,
        observacion: str,
        ip_usuario: str
    ) -> AuditResponse:
        try:
            # Validar token
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                user_id = payload.get("user_id")
                user = Usuario.objects.get(id=user_id)
                if not user.estado:
                    return AuditResponse(success=False, message="Usuario inactivo o token de usuario no existente")
            except (jwt.PyJWTError, Usuario.DoesNotExist):
                return AuditResponse(success=False, message="Token de acceso con firma invalida o usuario no existente")

            # Validar funcion
            try:
                funcion = Funcion.objects.get(id_funcion=id_funcion)
            except Funcion.DoesNotExist:
                return AuditResponse(success=False, message="id de funcion no existente")

            Auditoria.objects.create(
                username=user,
                id_funciones=funcion,
                accion=accion,
                descripcion=descripcion,
                observacion=f"IP: {ip_usuario} - {observacion}",
                estado_auditoria=True
            )
            return AuditResponse(success=True, message="La acción ha sido procesada con éxito")
        except Exception as e:
            return AuditResponse(success=False, message=str(e))


