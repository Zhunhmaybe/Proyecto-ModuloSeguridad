from users.models import Usuario

if not Usuario.objects.filter(user_name="admin").exists():
    user = Usuario.objects.create_superuser(
        user_name="admin", 
        email="admin@utn.edu.ec", 
        cedula="0000000000", 
        password="123"
    )
    print("Usuario administrador creado con éxito (admin / 123)")
else:
    print("El administrador ya existe.")
