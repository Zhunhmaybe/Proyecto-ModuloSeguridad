import strawberry

@strawberry.type
class ForgotPasswordResponse:
    success: bool
    message: str

def test():
    return ForgotPasswordResponse(success=True, message="Enlace enviado al correo.")
