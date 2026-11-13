# Práctica 2 - Tienda Online
# Autora: Lucía Pardo

"""Esquemas Pydantic de Usuario (peticiones y respuestas de la API)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from models.Usuario import Usuario

# Expresión regular sencilla para validar emails sin dependencias extra
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UsuarioCreate(BaseModel):
    """Datos que envía el cliente para crear un usuario."""

    nombre: str = Field(..., min_length=1, max_length=100, examples=["Ana García"])
    email: str = Field(..., pattern=EMAIL_REGEX, examples=["ana@correo.com"])
    tipo: Literal["cliente", "admin"] = Field("cliente", description="'cliente' o 'admin'")
    direccion_postal: Optional[str] = Field(
        None, max_length=200, examples=["Calle Mayor 1, 40001 Segovia"],
        description="Obligatoria para clientes",
    )

    @model_validator(mode="after")
    def comprobar_direccion(self):
        if self.tipo == "cliente" and not (self.direccion_postal and self.direccion_postal.strip()):
            raise ValueError("La dirección postal es obligatoria para los clientes")
        return self


class UsuarioRead(BaseModel):
    """Datos de un usuario que devuelve la API."""

    id: int
    nombre: str
    email: str
    es_admin: bool

    @classmethod
    def desde_modelo(cls, usuario: Usuario) -> "UsuarioRead":
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            es_admin=usuario.es_admin(),
        )
