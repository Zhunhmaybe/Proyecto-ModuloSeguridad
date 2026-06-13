from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from users.models import Usuario, Rol
from audit.models import Auditoria
from modules.models import Modulo
from .schema import validate_microsoft_token, generate_jwt

def login_view(request):
    if request.user.is_authenticated:
        is_admin = request.user.roles.filter(nombre_rol__icontains='admin').exists() or request.user.roles.filter(nombre_rol__icontains='seguridad').exists() or request.user.is_superuser
        return redirect('dashboard_admin' if is_admin else 'dashboard_user')
        
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = Usuario.objects.get(user_name=username)
            if not user.estado:
                error = "El usuario está inactivo (borrado lógico)."
            else:
                # Primero intentamos validación local de contraseña
                if user.check_password(password):
                    is_valid = True
                    ms_result = "Autenticación Local"
                else:
                    is_valid, ms_result = validate_microsoft_token(username, password)
                    
                if is_valid:
                    # Asignar backend explícitamente para iniciar sesión en la sesión de Django
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    auth_login(request, user)
                    
                    # Registrar auditoría de éxito
                    Auditoria.objects.create(
                        username=user,
                        accion="LOGIN EXITOSO (WEB)",
                        descripcion="Acceso web correcto desde portal unificado",
                        estado_auditoria=True
                    )
                    
                    # Generar JWT propio para consumo
                    token = generate_jwt(user)
                    
                    # Determinar si el usuario posee roles administrativos
                    is_admin = user.roles.filter(nombre_rol__icontains='admin').exists() or user.roles.filter(nombre_rol__icontains='seguridad').exists() or user.is_superuser
                    
                    response = redirect('dashboard_admin' if is_admin else 'dashboard_user')
                    # Guardar token JWT en cookies para poder leerlo desde el cliente/API
                    response.set_cookie('jwt_token', token, max_age=7200, httponly=False)
                    return response
                else:
                    # Registrar auditoría de fallo
                    Auditoria.objects.create(
                        username=user,
                        accion="LOGIN FALLIDO (WEB)",
                        descripcion=f"Intento web fallido: {ms_result}",
                        estado_auditoria=False
                    )
                    error = f"Contraseña incorrecta o error de autenticación: {ms_result}"
        except Usuario.DoesNotExist:
            error = "El usuario no está registrado en el Módulo de Seguridad."
            
    return render(request, 'login.html', {'error': error})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_user')
        
    error = None
    success = None
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        cedula = request.POST.get('cedula')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            error = "Las contraseñas no coinciden."
        elif len(password) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif Usuario.objects.filter(user_name=username).exists():
            error = "El usuario ya está registrado."
        elif Usuario.objects.filter(email=email).exists():
            error = "El correo ya está registrado."
        else:
            try:
                Usuario.objects.create_user(
                    user_name=username,
                    email=email,
                    cedula=cedula,
                    password=password
                )
                success = "Usuario registrado con éxito. Ahora puedes iniciar sesión."
            except Exception as e:
                error = f"Error al registrar: {str(e)}"
                
    return render(request, 'login.html', {
        'register_error': error, 
        'register_success': success, 
        'show_register': True
    })

def logout_view(request):
    auth_logout(request)
    response = redirect('login')
    response.delete_cookie('jwt_token')
    return response

@login_required(login_url='login')
def dashboard_user_view(request):
    token = request.COOKIES.get('jwt_token')
    return render(request, 'dashboard_user.html', {
        'user': request.user,
        'token': token
    })

@login_required(login_url='login')
def dashboard_admin_view(request):
    # Validar si el usuario tiene rol administrativo
    is_admin = request.user.roles.filter(nombre_rol__icontains='admin').exists() or request.user.roles.filter(nombre_rol__icontains='seguridad').exists() or request.user.is_superuser
    if not is_admin:
        return redirect('dashboard_user')
        
    token = request.COOKIES.get('jwt_token')
    
    # Estadísticas para el panel de control
    stats = {
        'total_users': Usuario.objects.count(),
        'active_users': Usuario.objects.filter(estado=True).count(),
        'total_roles': Rol.objects.count(),
        'total_modules': Modulo.objects.count(),
        'total_logs': Auditoria.objects.count()
    }
    
    # Obtener últimas 10 pistas de auditoría
    logs = Auditoria.objects.all().order_by('-fecha_creacion')[:10]
    
    return render(request, 'dashboard_admin.html', {
        'user': request.user,
        'token': token,
        'stats': stats,
        'logs': logs
    })
