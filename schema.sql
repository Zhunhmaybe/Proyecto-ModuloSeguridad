-- =========================================================================
-- Script DDL para Módulo de Seguridades en PostgreSQL
-- IMPORTANTE: En Django, lo ideal es dejar que el ORM (python manage.py migrate)
-- cree estas tablas automáticamente. Sin embargo, aquí tienes el SQL puro.
-- =========================================================================

-- Tabla: Usuario
CREATE TABLE Usuario (
    id SERIAL PRIMARY KEY, -- Agregado para usar como FK en Roles_usuario según estándar
    user_name VARCHAR(16) UNIQUE NOT NULL,
    cedula VARCHAR(10) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Roles
CREATE TABLE Roles (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(100) NOT NULL,
    estado_rol BOOLEAN DEFAULT TRUE
);

-- Tabla: Roles_usuario (Relación Muchos a Muchos)
CREATE TABLE Roles_usuario (
    id SERIAL PRIMARY KEY,
    id_rol INT NOT NULL,
    id_user INT NOT NULL,
    CONSTRAINT fk_rol FOREIGN KEY (id_rol) REFERENCES Roles(id_rol) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (id_user) REFERENCES Usuario(id) ON DELETE CASCADE,
    UNIQUE (id_rol, id_user)
);

-- Tabla: Modulos
CREATE TABLE Modulos (
    id_modulo SERIAL PRIMARY KEY,
    nombre_modulo VARCHAR(100) NOT NULL,
    descripcion_modulo TEXT,
    estado_modulo BOOLEAN DEFAULT TRUE
);

-- Tabla: Funciones
CREATE TABLE Funciones (
    id_funcion SERIAL PRIMARY KEY,
    nombre_funcion VARCHAR(100) NOT NULL,
    estado_funcion BOOLEAN DEFAULT TRUE
);

-- Tabla: modulos_funciones (Relación Muchos a Muchos)
CREATE TABLE modulos_funciones (
    id SERIAL PRIMARY KEY,
    id_modulo INT NOT NULL,
    id_funcion INT NOT NULL,
    CONSTRAINT fk_modulo_func FOREIGN KEY (id_modulo) REFERENCES Modulos(id_modulo) ON DELETE CASCADE,
    CONSTRAINT fk_funcion_mod FOREIGN KEY (id_funcion) REFERENCES Funciones(id_funcion) ON DELETE CASCADE,
    UNIQUE (id_modulo, id_funcion)
);

-- Tabla: roles_funciones (Relación Muchos a Muchos)
CREATE TABLE roles_funciones (
    id SERIAL PRIMARY KEY,
    id_rol INT NOT NULL,
    id_funciones INT NOT NULL,
    CONSTRAINT fk_rol_func FOREIGN KEY (id_rol) REFERENCES Roles(id_rol) ON DELETE CASCADE,
    CONSTRAINT fk_funcion_rol FOREIGN KEY (id_funciones) REFERENCES Funciones(id_funcion) ON DELETE CASCADE,
    UNIQUE (id_rol, id_funciones)
);

-- Tabla: Auditorias
CREATE TABLE Auditorias (
    id_auditoria SERIAL PRIMARY KEY,
    username VARCHAR(16) NOT NULL, -- FK a user_name
    id_funciones INT NOT NULL,     -- FK a Funciones
    accion VARCHAR(255) NOT NULL,
    descripcion TEXT,
    observacion TEXT,
    estado_auditoria BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (username) REFERENCES Usuario(user_name) ON DELETE SET NULL,
    CONSTRAINT fk_audit_funcion FOREIGN KEY (id_funciones) REFERENCES Funciones(id_funcion) ON DELETE SET NULL
);
