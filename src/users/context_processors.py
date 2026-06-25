from users.models import Funcion

def user_functions(request):
    if request.user.is_authenticated:
        # Extraer nombres de las funciones habilitadas (a nivel global)
        # que además estén asignadas a través de los roles del usuario.
        funciones = Funcion.objects.filter(
            estado_funcion=True,
            roles__usuarios=request.user
        ).values_list('nombre_funcion', flat=True).distinct()
        return {'user_active_functions': list(funciones)}
    return {'user_active_functions': []}
