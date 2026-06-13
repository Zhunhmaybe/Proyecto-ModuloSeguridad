import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Usuario, Rol
from modules.models import Modulo, Funcion

def populate():
    print("Iniciando la inserción de datos de prueba...")

    # 1. Crear Módulos
    modulos_data = [
        {"nombre": "Compras", "desc": "Gestión de órdenes de compra, proveedores y adquisiciones."},
        {"nombre": "Facturación", "desc": "Emisión de facturas, notas de crédito y control de ventas."},
        {"nombre": "Inventario", "desc": "Control de stock, bodegas, ingresos y salidas de mercancía."},
        {"nombre": "Cuentas por Cobrar", "desc": "Gestión de cobros, clientes y saldos pendientes."}
    ]
    
    modulos = {}
    for m in modulos_data:
        mod, created = Modulo.objects.get_or_create(
            nombre_modulo=m["nombre"],
            defaults={"descripcion_modulo": m["desc"], "estado_modulo": True}
        )
        modulos[m["nombre"]] = mod
        if created:
            print(f"Módulo creado: {m['nombre']}")

    # 2. Crear Funciones (Permisos)
    funciones_data = [
        # Compras
        {"nombre": "CREAR_ORDEN", "modulo": "Compras"},
        {"nombre": "APROBAR_ORDEN", "modulo": "Compras"},
        # Facturación
        {"nombre": "EMITIR_FACTURA", "modulo": "Facturación"},
        {"nombre": "ANULAR_FACTURA", "modulo": "Facturación"},
        # Inventario
        {"nombre": "REGISTRAR_PRODUCTO", "modulo": "Inventario"},
        {"nombre": "ACTUALIZAR_STOCK", "modulo": "Inventario"},
    ]

    funciones = {}
    for f in funciones_data:
        func, created = Funcion.objects.get_or_create(
            nombre_funcion=f["nombre"],
            defaults={"estado_funcion": True}
        )
        # Asociar al módulo
        mod = modulos[f["modulo"]]
        func.modulos.add(mod)
        funciones[f["nombre"]] = func
        if created:
            print(f"Función creada: {f['nombre']} asociada al módulo {f['modulo']}")

    # 3. Crear Roles
    roles_data = [
        {"nombre": "Administrador de Seguridad", "funciones": ["CREAR_ORDEN", "APROBAR_ORDEN", "EMITIR_FACTURA", "ANULAR_FACTURA", "REGISTRAR_PRODUCTO", "ACTUALIZAR_STOCK"]},
        {"nombre": "Gerente de Compras", "funciones": ["CREAR_ORDEN", "APROBAR_ORDEN"]},
        {"nombre": "Facturador", "funciones": ["EMITIR_FACTURA"]},
        {"nombre": "Auxiliar de Bodega", "funciones": ["REGISTRAR_PRODUCTO", "ACTUALIZAR_STOCK"]}
    ]

    roles = {}
    for r in roles_data:
        rol, created = Rol.objects.get_or_create(
            nombre_rol=r["nombre"],
            defaults={"estado_rol": True}
        )
        # Asociar funciones
        for fn_name in r["funciones"]:
            rol.funciones.add(funciones[fn_name])
        roles[r["nombre"]] = rol
        if created:
            print(f"Rol creado: {r['nombre']} con sus permisos correspondientes")

    # 4. Crear Superusuario (si no existe) y asignarle el rol de admin
    admin_user, created = Usuario.objects.get_or_create(
        user_name="admin",
        defaults={
            "email": "admin@utn.edu.ec",
            "cedula": "0000000000",
            "is_staff": True,
            "is_superuser": True,
            "estado": True
        }
    )
    if created:
        admin_user.set_password("123")
        admin_user.save()
        print("Superusuario 'admin' creado con contraseña '123'")
    
    # Asignar rol de seguridad al admin
    admin_user.roles.add(roles["Administrador de Seguridad"])
    print("Rol 'Administrador de Seguridad' asignado al superusuario 'admin'")

    # 5. Crear un usuario de prueba normal (no admin)
    user_test, created = Usuario.objects.get_or_create(
        user_name="compras_user",
        defaults={
            "email": "compras@utn.edu.ec",
            "cedula": "1234567890",
            "is_staff": False,
            "is_superuser": False,
            "estado": True
        }
    )
    if created:
        user_test.set_password("123")
        user_test.save()
        print("Usuario normal 'compras_user' creado con contraseña '123'")
    
    # Asignar rol de compras
    user_test.roles.add(roles["Gerente de Compras"])
    print("Rol 'Gerente de Compras' asignado al usuario 'compras_user'")

    print("\n¡Población de base de datos finalizada con éxito!")

if __name__ == "__main__":
    populate()
