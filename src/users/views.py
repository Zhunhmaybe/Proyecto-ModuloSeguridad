from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from users.models import Usuario, Rol, PasswordResetToken
from audit.models import Auditoria
from modules.models import Modulo
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
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
        import re
        from django.db import IntegrityError
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        cedula = request.POST.get('cedula')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            error = "Las contraseñas no coinciden."
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@(gmail\.com|utn\.edu\.ec)$', email):
            error = "Solo se permiten correos @gmail.com o @utn.edu.ec."
        elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[@$!%*?&\.\-\_])[A-Za-z\d@$!%*?&\.\-\_]{8,}$', password):
            error = "La contraseña debe tener 8+ caracteres, mayúscula, minúscula y un carácter especial (@$!%*?&.-_)."
        elif Usuario.objects.filter(user_name=username).exists():
            error = "El nombre de usuario ya está registrado."
        elif Usuario.objects.filter(email=email).exists():
            error = "El correo electrónico ya está registrado."
        else:
            try:
                user = Usuario.objects.create_user(
                    user_name=username,
                    email=email,
                    cedula=cedula,
                    password=password
                )
                
                from users.models import EmailVerificationToken
                from django.core.mail import send_mail
                from django.conf import settings
                
                token = EmailVerificationToken.objects.create(usuario=user)
                verify_url = request.build_absolute_uri(reverse('verify_email', args=[str(token.token)]))
                
                try:
                    send_mail(
                        subject='Bienvenido - Verifica tu correo',
                        message=f'Hola {user.user_name},\n\nGracias por registrarte en Seguridad Centralizada. Por favor verifica tu correo electrónico haciendo clic en el siguiente enlace:\n{verify_url}',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception:
                    pass # Evitamos romper el flujo si el correo falla
                    
                success = "Usuario registrado con éxito. Revisa tu correo electrónico para verificar tu cuenta e iniciar sesión."
                # Al tener éxito, renderizamos login.html sin el flag show_register,
                # para que se posicione directamente en la pestaña de Iniciar Sesión.
                return render(request, 'login.html', {
                    'register_success': success
                })
            except IntegrityError as e:
                error_msg = str(e).lower()
                if 'cedula_valida' in error_msg:
                    error = "La cédula ingresada no es válida en Ecuador."
                elif 'cedula' in error_msg:
                    error = "Esta cédula ya se encuentra registrada."
                else:
                    error = "Error de base de datos: Verifica tus datos."
            except Exception as e:
                error = f"Error general al registrar: {str(e)}"
                
    return render(request, 'login.html', {
        'register_error': error, 
        'show_register': True
    })

def logout_view(request):
    auth_logout(request)
    response = redirect('login')
    response.delete_cookie('jwt_token')
    return response

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Usuario.objects.get(email=email)
            token = PasswordResetToken.objects.create(usuario=user)
            
            # Construir URL de reseteo
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[str(token.token)]))
            
            # Enviar correo
            try:
                send_mail(
                    subject='Recuperación de Contraseña - Seguridad Centralizada',
                    message=f'Hola {user.user_name},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_url}\n\nSi no solicitaste esto, ignora este correo.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                success = "Te hemos enviado un enlace de recuperación a tu correo."
            except Exception as e:
                success = f"El token se generó ({reset_url}) pero falló el envío de email: {str(e)}"
                
            return render(request, 'login.html', {'register_success': success, 'show_forgot': True})
            
        except Usuario.DoesNotExist:
            error = "No existe ningún usuario con este correo institucional."
            return render(request, 'login.html', {'register_error': error, 'show_forgot': True})
            
    return redirect('login')

def verify_email_view(request, token):
    from users.models import EmailVerificationToken
    try:
        verification_token = EmailVerificationToken.objects.get(token=token, usado=False)
        user = verification_token.usuario
        user.correo_verificado = True
        user.save()
        
        verification_token.usado = True
        verification_token.save()
        
        return render(request, 'login.html', {
            'register_success': '¡Correo verificado exitosamente! Ya puedes iniciar sesión.'
        })
    except EmailVerificationToken.DoesNotExist:
        return render(request, 'login.html', {
            'error': 'El enlace de verificación es inválido o ya fue utilizado.'
        })

def reset_password_view(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token, usado=False)
    except PasswordResetToken.DoesNotExist:
        return render(request, 'reset_password.html', {'error': 'El enlace de recuperación es inválido o ya fue utilizado.'})

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            return render(request, 'reset_password.html', {'error': 'Las contraseñas no coinciden.', 'token': token})
        
        if len(password) < 8:
            return render(request, 'reset_password.html', {'error': 'La contraseña debe tener al menos 8 caracteres.', 'token': token})
            
        # Actualizar contraseña
        user = reset_token.usuario
        user.set_password(password)
        user.save()
        
        # Marcar token como usado
        reset_token.usado = True
        reset_token.save()
        
        return render(request, 'login.html', {'register_success': 'Contraseña actualizada con éxito. Ahora puedes iniciar sesión.'})

    return render(request, 'reset_password.html', {'token': token})

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
