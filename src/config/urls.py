from django.urls import path
from strawberry.django.views import GraphQLView
from .schema import schema
from django.views.decorators.csrf import csrf_exempt
from users import views as user_views

urlpatterns = [
    # path('admin/', admin.site.urls), # Deshabilitado por seguridad e inicio unificado
    path('', user_views.login_view, name='login'),
    path('login/', user_views.login_view, name='login_alias'),
    path('register/', user_views.register_view, name='register'),
    path('dashboard/user/', user_views.dashboard_user_view, name='dashboard_user'),
    path('dashboard/admin/', user_views.dashboard_admin_view, name='dashboard_admin'),
    path('logout/', user_views.logout_view, name='logout'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(schema=schema))),
]
