import json
import os
import psycopg2
import jwt
from datetime import datetime, timedelta, timezone
from django.contrib.auth.hashers import check_password  # Verifica hashes PBKDF2 de Django

# ---------------------------------------------------------------------------
# Variables de entorno
# ---------------------------------------------------------------------------
DB_URL     = os.environ.get('DB_URL', 'postgresql://postgres.tterpmyretkigqazruor:c95$ZTbKNjeF&Gd@aws-1-us-east-1.pooler.supabase.com:5432/postgres')
JWT_SECRET = os.environ.get('JWT_SECRET', 'django-insecure-d)&w*0vqn-lr%)-2i=be^wcn6$&jeccw+l8&cyl@+y8fg10tbp')

# ---------------------------------------------------------------------------
# API Keys válidas por módulo externo
# ---------------------------------------------------------------------------
API_KEYS_VALIDAS = {
    "dev_key_cxc_111":         "CXC",
    "dev_key_facturacion_222": "FACTURACION",
    "dev_key_inventario_333":  "INVENTARIO",
    "dev_key_compras_444":     "COMPRAS",
    "dev_key_seguridad_555":   "SEGURIDAD",
}


def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}')) if 'body' in event else event

        api_key    = body.get('api_key')
        usuario    = body.get('usuario')
        clave      = body.get('clave')
        ip_usuario = body.get('ip')

        if not all([api_key, usuario, clave, ip_usuario]):
            return respond(400, False, "Faltan parámetros (api_key, usuario, clave, ip)")

        # 1. Validar la identidad del módulo
        modulo = API_KEYS_VALIDAS.get(api_key)
        if not modulo:
            return respond(401, False, "API Key del módulo inválida o no autorizada")

        conn   = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        # 2. Control de Fuerza Bruta
        cursor.execute(
            "SELECT intentos_fallidos, ultimo_intento FROM control_ips WHERE ip_usuario = %s",
            (ip_usuario,)
        )
        registro = cursor.fetchone()

        if registro:
            intentos, ultimo_intento = registro
            ahora        = datetime.now()
            tiempo_pasado = ahora - ultimo_intento

            if intentos >= 5:
                if tiempo_pasado < timedelta(minutes=3):
                    segundos_restantes = int((timedelta(minutes=3) - tiempo_pasado).total_seconds())
                    minutos  = segundos_restantes // 60
                    segundos = segundos_restantes % 60
                    return respond(429, False, f"Demasiados intentos. Intente en {minutos}m {segundos}s.")
                else:
                    # Cumplió el castigo, reiniciar contador
                    cursor.execute(
                        "UPDATE control_ips SET intentos_fallidos = 0 WHERE ip_usuario = %s",
                        (ip_usuario,)
                    )
                    conn.commit()

        # 3. Buscar usuario y traer el hash de la contraseña
        #    ⚠️  NO comparamos la clave en el SQL — la traemos y la verificamos en Python
        cursor.execute(
            "SELECT id, password, estado FROM usuarios WHERE user_name = %s",
            (usuario,)
        )
        fila = cursor.fetchone()

        if not fila:
            # No revelamos si el usuario existe (seguridad)
            _sumar_intento(cursor, conn, ip_usuario)
            return respond(401, False, "Usuario o contraseña incorrectos")

        user_id, password_hash, estado = fila

        if not estado:
            return respond(401, False, "Usuario inactivo")

        # 4. Verificar la contraseña contra el hash PBKDF2 de Django
        #    check_password("clave_en_texto", "pbkdf2_sha256$...") → True/False
        if not check_password(clave, password_hash):
            _sumar_intento(cursor, conn, ip_usuario)
            _registrar_auditoria(cursor, conn, usuario, "LOGIN FALLIDO",
                                 f"Intento fallido desde {ip_usuario}", modulo, False)
            return respond(401, False, "Usuario o contraseña incorrectos")

        # 5. Login exitoso: limpiar historial de errores
        cursor.execute("DELETE FROM control_ips WHERE ip_usuario = %s", (ip_usuario,))
        conn.commit()

        # 6. Pista de auditoría: éxito
        _registrar_auditoria(cursor, conn, usuario, "LOGIN EXITOSO",
                              f"Autenticación exitosa desde {ip_usuario}", modulo, True)

        cursor.close()
        conn.close()

        # 7. Generar el JWT maestro (8 horas de sesión)
        caducidad = datetime.now(timezone.utc) + timedelta(hours=8)
        payload = {
            "user_id":       user_id,
            "user_name":     usuario,
            "modulo_origen": modulo,
            "exp":           caducidad,
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return respond(200, True, "Autenticación exitosa", token=token)

    except Exception as e:
        print(f"Error interno: {str(e)}")
        return respond(500, False, "Error interno del servidor")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sumar_intento(cursor, conn, ip_usuario):
    """Incrementa el contador de intentos fallidos para una IP."""
    cursor.execute("""
        INSERT INTO control_ips (ip_usuario, intentos_fallidos, ultimo_intento)
        VALUES (%s, 1, NOW())
        ON CONFLICT (ip_usuario)
        DO UPDATE SET
            intentos_fallidos = control_ips.intentos_fallidos + 1,
            ultimo_intento = NOW()
    """, (ip_usuario,))
    conn.commit()


def _registrar_auditoria(cursor, conn, username, accion, descripcion, modulo, estado):
    """Inserta una pista de auditoría en la tabla auditoria."""
    cursor.execute("""
        INSERT INTO auditoria (username, accion, descripcion, estado_auditoria, modulo, fecha_creacion)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (username, accion, descripcion, estado, modulo))
    conn.commit()


def respond(status_code, success, message, token=None):
    body_dict = {'success': success, 'message': message}
    if token:
        body_dict['token'] = token
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body_dict)
    }
