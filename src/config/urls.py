from django.urls import path
from strawberry.django.views import GraphQLView
from .schema import schema
from django.views.decorators.csrf import csrf_exempt

from users import views as user_views
from modules import views as module_views



urlpatterns = [

    path(
        '',
        user_views.login_view,
        name='login'
    ),


    path(
        'login/',
        user_views.login_view,
        name='login_alias'
    ),


    path(
        'register/',
        user_views.register_view,
        name='register'
    ),



    path(
        'dashboard/user/',
        user_views.dashboard_user_view,
        name='dashboard_user'
    ),



    path(
        'dashboard/admin/',
        user_views.dashboard_admin_view,
        name='dashboard_admin'
    ),



    path(
        'logout/',
        user_views.logout_view,
        name='logout'
    ),



    path(
        'graphql/',
        csrf_exempt(
            GraphQLView.as_view(schema=schema)
        )
    ),





    # =====================
    # CRUD ROLES
    # =====================


    path(
        'roles/',
        user_views.roles_view,
        name='roles'
    ),


    path(
        'roles/editar/<int:id>/',
        user_views.editar_rol,
        name='editar_rol'
    ),




    # =====================
    # CRUD MODULOS
    # =====================


    path(
        'modulos/',
        module_views.modulos_view,
        name='modulos'
    ),

    #Usuarios
    path(
    'usuarios/',
    user_views.usuarios_view,
    name='usuarios'
),
path(
    'usuarios/editar/<int:id>/',
    user_views.editar_usuario,
    name='editar_usuario'
),

#Funciones
path(
    'funciones/',
    user_views.funciones_view,
    name='funciones'
),


path(
    'funciones/editar/<int:id>/',
    user_views.editar_funcion,
    name='editar_funcion'
),


]