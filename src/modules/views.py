from django.shortcuts import render, redirect, get_object_or_404
from .models import Modulo
from users.models import Funcion, Rol


def modulos_view(request):
    modulos = Modulo.objects.all().prefetch_related('funciones').order_by('-id_modulo')
    roles = Rol.objects.filter(estado_rol=True)
    todas_funciones = Funcion.objects.filter(estado_funcion=True)

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'create_module':
            nombre = request.POST.get('nombre_modulo', '').strip()
            descripcion = request.POST.get('descripcion_modulo', '').strip()
            funciones_ids = request.POST.getlist('funciones')

            ctx = {'modulos': modulos, 'roles': roles, 'todas_funciones': todas_funciones}

            if not nombre:
                ctx['error'] = 'El nombre del módulo es obligatorio.'
                return render(request, 'modulos.html', ctx)


            if Modulo.objects.filter(nombre_modulo__iexact=nombre).exists():
                ctx['error'] = 'Ya existe un módulo con ese nombre.'
                return render(request, 'modulos.html', ctx)

            modulo = Modulo.objects.create(
                nombre_modulo=nombre,
                descripcion_modulo=descripcion,
                estado_modulo=True
            )
            if funciones_ids:
                Funcion.objects.filter(id_funcion__in=funciones_ids).update(modulo=modulo)

        elif action == 'toggle_module_status':
            mod_id = request.POST.get('module_id')
            try:
                mod = Modulo.objects.get(id_modulo=mod_id)
                mod.estado_modulo = not mod.estado_modulo
                mod.save()
            except Modulo.DoesNotExist:
                pass

        return redirect('modulos')

    return render(request, 'modulos.html', {
        'modulos': modulos,
        'roles': roles,
        'todas_funciones': todas_funciones,
    })


def editar_modulo(request, id):
    modulo = get_object_or_404(Modulo, id_modulo=id)
    roles = Rol.objects.filter(estado_rol=True).prefetch_related('funciones')
    roles_actuales_ids = set(modulo.roles.values_list('id_rol', flat=True))

    if request.method == "POST":
        action = request.POST.get('action', 'edit_module')

        if action == 'assign_roles':
            roles_ids = request.POST.getlist('roles')
            Rol.objects.filter(modulo=modulo).update(modulo=None)
            if roles_ids:
                Rol.objects.filter(id_rol__in=roles_ids).update(modulo=modulo)
            return redirect('editar_modulo', id=modulo.id_modulo)

        elif action == 'edit_module':
            nombre = request.POST.get('nombre_modulo', '').strip()
            descripcion = request.POST.get('descripcion_modulo', '').strip()
            estado = request.POST.get('estado_modulo') == 'true'
            funciones_ids = request.POST.getlist('funciones')

            ctx = {'modulo': modulo, 'roles': roles, 'roles_actuales_ids': roles_actuales_ids}

            if not nombre:
                ctx['error'] = 'El nombre del módulo es obligatorio.'
                return render(request, 'editar_modulo.html', ctx)

            if Modulo.objects.filter(nombre_modulo__iexact=nombre).exclude(id_modulo=id).exists():
                ctx['error'] = 'Ya existe un módulo con ese nombre.'
                return render(request, 'editar_modulo.html', ctx)

            modulo.nombre_modulo = nombre
            modulo.descripcion_modulo = descripcion
            modulo.estado_modulo = estado
            modulo.save()
            
            Funcion.objects.filter(modulo=modulo).update(modulo=None)
            if funciones_ids:
                Funcion.objects.filter(id_funcion__in=funciones_ids).update(modulo=modulo)

            return redirect('modulos')

    # Recalcular con IDs actuales para el template
    roles_actuales_ids = set(modulo.roles.values_list('id_rol', flat=True))
    # Obtener todos los roles activos para el modal
    todos_roles = Rol.objects.filter(estado_rol=True)
    
    todas_funciones = Funcion.objects.filter(estado_funcion=True)
    funciones_actuales_ids = set(modulo.funciones.values_list('id_funcion', flat=True))
    
    return render(request, 'editar_modulo.html', {
        'modulo': modulo,
        'roles_actuales_ids': roles_actuales_ids,
        'todos_roles': todos_roles,
        'todas_funciones': todas_funciones,
        'funciones_actuales_ids': funciones_actuales_ids,
    })

