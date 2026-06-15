from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from users.models import Usuario, Rol
from audit.models import Auditoria
from django.shortcuts import get_object_or_404
from .models import Rol, Funcion, FuncionRol
from modules.models import Modulo
from modules.models import Funcion
from .schema import validate_microsoft_token, generate_jwt

@login_required(login_url='login')
def roles_view(request):

    roles = Rol.objects.all()

    funciones = Funcion.objects.filter(
        estado_funcion=True
    )


    if request.method == "POST":


        nombre = request.POST.get(
            "nombre_rol"
        )


        funciones_seleccionadas = request.POST.getlist(
            "funciones"
        )



        rol = Rol.objects.create(

            nombre_rol=nombre,

            estado_rol=True

        )



        for f in funciones_seleccionadas:


            FuncionRol.objects.create(

                rol=rol,

                funcion_id=f

            )



        return redirect('roles')



    return render(

        request,

        'roles.html',

        {

        'roles':roles,

        'funciones':funciones

        }

    )

@login_required(login_url='login')
def editar_rol(request,id):


    rol = get_object_or_404(
        Rol,
        id_rol=id
    )


    funciones = Funcion.objects.all()



    if request.method=="POST":


        rol.nombre_rol = request.POST.get(
            "nombre_rol"
        )


        rol.save()



        rol.funciones.clear()



        for f in request.POST.getlist(
            "funciones"
        ):


            FuncionRol.objects.create(

                rol=rol,

                funcion_id=f

            )



        return redirect(
            'roles'
        )



    return render(

        request,

        'editar_rol.html',

        {

        'rol':rol,

        'funciones':funciones

        }

    )
#Usuarios
@login_required(login_url='login')
def usuarios_view(request):


    permiso = Funcion.objects.filter(

        nombre_funcion="GESTIONAR_USUARIOS",

        roles__usuarios=request.user,

        estado_funcion=True

    ).exists()



    if not permiso:

        return redirect(
            'dashboard_user'
        )



    usuarios = Usuario.objects.all()



    return render(

        request,

        'usuarios.html',

        {

        'usuarios':usuarios

        }

    )

@login_required(login_url='login')
def editar_usuario(request, id):


    usuario = get_object_or_404(
        Usuario,
        id=id
    )


    if request.method == "POST":


        usuario.user_name = request.POST.get(
            'user_name'
        )


        usuario.email = request.POST.get(
            'email'
        )


        usuario.estado = True if request.POST.get(
            'estado'
        ) else False



        usuario.save()



        # actualizar roles

        roles = request.POST.getlist(
            'roles'
        )


        usuario.roles.clear()


        for rol_id in roles:

            rol = Rol.objects.get(
                id_rol=rol_id
            )

            usuario.roles.add(
                rol
            )


        return redirect(
            'usuarios'
        )



    roles = Rol.objects.filter(
        estado_rol=True
    )


    return render(

        request,

        'editar_usuario.html',

        {

        'usuario':usuario,

        'roles':roles

        }

    )
#Funciones
@login_required(login_url='login')
def funciones_view(request):

    permiso = Funcion.objects.filter(

        nombre_funcion="GESTIONAR_ROLES",

        roles__usuarios=request.user,

        estado_funcion=True

    ).exists()


    if not permiso:

        return redirect('dashboard_user')



    if request.method == "POST":


        nombre = request.POST.get(
            'nombre_funcion'
        )


        estado = True if request.POST.get(
            'estado'
        ) else False



        Funcion.objects.create(

            nombre_funcion=nombre,

            estado_funcion=estado

        )


        return redirect(
            'funciones'
        )




    funciones = Funcion.objects.all()



    return render(

        request,

        'funciones.html',

        {

        'funciones':funciones

        }

    )
@login_required(login_url='login')
def editar_funcion(request,id):


    funcion = get_object_or_404(

        Funcion,

        id_funcion=id

    )



    if request.method == "POST":



        funcion.nombre_funcion = request.POST.get(
            'nombre_funcion'
        )


        funcion.estado_funcion = True if request.POST.get(
            'estado'
        ) else False



        funcion.save()



        return redirect(
            'funciones'
        )




    return render(

        request,

        'editar_funcion.html',

        {

        'funcion':funcion

        }

    )
#Login
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
#Modulos
from modules.models import Modulo


@login_required(login_url='login')
def modulos_view(request):


    if request.method == "POST":


        nombre = request.POST.get('nombre_modulo')

        descripcion = request.POST.get('descripcion_modulo')

        estado = request.POST.get('estado_modulo')


        return redirect('modulos')





    modulos = Modulo.objects.all()



    return render(

        request,

        'modulos.html',

        {

            'modulos': modulos

        }

    )

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


    funciones_usuario = Funcion.objects.filter(

        roles__usuarios=request.user,

        estado_funcion=True

    ).distinct()



    stats = {

        'total_users': Usuario.objects.count(),

        'active_users': Usuario.objects.filter(
            estado=True
        ).count(),

        'total_roles': Rol.objects.count(),

        'total_modules': Modulo.objects.count(),

        'total_logs': Auditoria.objects.count()

    }



    logs = Auditoria.objects.all().order_by(
        '-fecha_creacion'
    )[:10]



    return render(

        request,

        'dashboard_admin.html',

        {

        'user':request.user,

        'stats':stats,

        'logs':logs,

        'funciones':funciones_usuario

        }

    )