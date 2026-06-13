import strawberry
from typing import List, Optional
from users.models import Usuario, Rol
from audit.models import Auditoria
from modules.models import Modulo
import os
import msal
import jwt
import datetime

# --- JWT Config ---
JWT_SECRET = os.getenv('SECRET_KEY', 'secret')

def generate_jwt(user_id, user_name):
    payload = {
        'user_id': user_id,
        'user_name': user_name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2) # Token válido por 2 horas
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
        return False, "Credenciales inválidas (Modo Prueba)"

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
class RolType:
    id_rol: int
    nombre_rol: str
    estado_rol: bool

@strawberry.type
class UsuarioType:
    id: int
    user_name: str
    email: str
    cedula: str
    estado: bool

@strawberry.type
class LoginResponse:
    success: bool
    token: Optional[str]
    message: Optional[str]
    # actions: List[str] # Lista de permisos para HU7 (Opcional, se puede ampliar)
    
#Registrar Usuario
@strawberry.type
class RegisterResponse:
    success: bool
    message: str
#Recuperar Contraseña
@strawberry.type
class ForgotPasswordResponse:
    success: bool
    message: str
@strawberry.type
class Query:
    @strawberry.field
    def usuarios(self) -> List[UsuarioType]:
        # Convierte los modelos ORM a tipos de Strawberry
        users = Usuario.objects.all()
        return [
            UsuarioType(
                id=u.id, user_name=u.user_name, email=u.email, 
                cedula=u.cedula, estado=u.estado
            ) for u in users
        ]

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

            # 2. Validar con Microsoft Entra ID (MSAL) - HU8 / HU7
            is_valid, ms_result = validate_microsoft_token(username, password)
            if not is_valid:
                # HU8: CA2 - Guardar pista de auditoría en intento fallido
                Auditoria.objects.create(
                    username=user,
                    accion="LOGIN FALLIDO",
                    descripcion=f"Intento fallido con Microsoft: {ms_result}",
                    estado_auditoria=False
                )
                return LoginResponse(success=False, token=None, message=f"Fallo auth MS: {ms_result}")
            
            # 3. Generar JWT propio para los demás módulos
            token = generate_jwt(user.id, user.user_name)
            
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
        username:str,
        email:str,
        cedula:str,
        password:str,
        confirm_password:str
    )-> RegisterResponse:

        if Usuario.objects.filter(user_name=username).exists():
            return RegisterResponse(
                success=False,
                message="El usuario ya existe"
            )

        if Usuario.objects.filter(email=email).exists():
            return RegisterResponse(
                success=False,
                message="El correo ya está registrado"
            )
        if len(password) < 8:
            return RegisterResponse(
                success=False,
                message="La contraseña debe tener al menos 8 caracteres"
        )
        if password != confirm_password:
            return RegisterResponse(
                success=False,
            message="Las contraseñas no coinciden"
        )

        Usuario.objects.create_user(
            user_name=username,
            email=email,
            cedula=cedula,
            password=password
        )

        return RegisterResponse(
            success=True,
            message="Usuario registrado correctamente"
        )
    @strawberry.mutation
    def forgot_password(
        self,
        email:str
    ) -> ForgotPasswordResponse:

        try:

            user = Usuario.objects.get(email=email)

            token = PasswordResetToken.objects.create(
                usuario=user
            )

            return ForgotPasswordResponse(
                success=True,
                message=str(token.token)
            )

        except Usuario.DoesNotExist:

            return ForgotPasswordResponse(
                success=False,
                message="Correo no registrado"
            )


