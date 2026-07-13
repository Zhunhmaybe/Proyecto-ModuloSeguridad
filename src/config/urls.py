# pyrefly: ignore [missing-import]
from django.urls import path
# pyrefly: ignore [missing-import]
from strawberry.django.views import GraphQLView
from .schema import schema
# pyrefly: ignore [missing-import]
from django.views.decorators.csrf import csrf_exempt

from users import views as user_views
from users import reports as user_reports
from modules import views as module_views



urlpatterns = [

    # path('admin/', admin.site.urls), # Deshabilitado por seguridad e inicio unificado
    path('', user_views.login_view, name='login'),
    path('login/', user_views.login_view, name='login_alias'),
    # Registro público deshabilitado - redirige al login
    path('register/', user_views.login_view, name='register'),
    path('forgot-password/', user_views.forgot_password_view, name='forgot_password'),
    path('verify-code/', user_views.verify_reset_code_view, name='verify_reset_code'),
    path('reset-password/', user_views.reset_password_view, name='reset_password'),
    path('verify-email/<uuid:token>/', user_views.verify_email_view, name='verify_email'),
    path('dashboard/user/', user_views.dashboard_user_view, name='dashboard_user'),
    path('dashboard/admin/', user_views.dashboard_admin_view, name='dashboard_admin'),
    path('logout/', user_views.logout_view, name='logout'),
    path('exportar-reporte/<str:tipo>/', user_views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(schema=schema))),

    # =====================
    # API REST - El Guardia
    # =====================
    path('api/auth/login/', user_views.api_auth_login, name='api_auth_login'),
    path('api/auth/forgot-password/', user_views.api_forgot_password, name='api_forgot_password'),
    path('api/auth/verify-code/', user_views.api_verify_code, name='api_verify_code'),
    path('api/auth/reset-password/', user_views.api_reset_password, name='api_reset_password'),
    
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

    path(
        'modulos/editar/<int:id>/',
        module_views.editar_modulo,
        name='editar_modulo'
    ),


    path(
    'usuarios/',
    user_views.usuarios_view,
    name='usuarios'
),
path(
    'gestion/',
    user_views.gestion_view,
    name='gestion'
),
path(
    'usuarios/crear/',
    user_views.crear_usuario,
    name='crear_usuario'
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

# Reportes
path('reportes/roles/', user_reports.report_roles, name='report_roles'),
path('reportes/usuarios/', user_reports.report_usuarios, name='report_usuarios'),
path('reportes/modulos/', user_reports.report_modulos, name='report_modulos'),
path('reportes/auditoria/', user_reports.report_auditoria, name='report_auditoria'),

]
