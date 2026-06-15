from django.shortcuts import render,redirect,get_object_or_404
from .models import Modulo, FuncionModulo
from users.models import Funcion

# Create your views here.
def modulos_view(request):


    modulos = Modulo.objects.all()


    funciones = Funcion.objects.all()



    if request.method=="POST":


        nombre = request.POST.get(
            "nombre_modulo"
        )


        descripcion = request.POST.get(
            "descripcion_modulo"
        )



        modulo = Modulo.objects.create(

            nombre_modulo=nombre,

            descripcion_modulo=descripcion,

            estado_modulo=True

        )



        for f in request.POST.getlist(
            "funciones"
        ):


            FuncionModulo.objects.create(

                modulo=modulo,

                funcion_id=f

            )



        return redirect(
            'modulos'
        )



    return render(

        request,

        'modulos.html',

        {

        'modulos':modulos,

        'funciones':funciones

        }

    )
