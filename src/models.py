
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,  relationship
from collections import OrderedDict
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)

    # relationship("Favoritos", back_populates="usuario") --> se relacion con la clase Favoritos a traves del atributo usuario
    favoritos: Mapped[list["Favoritos"]] = relationship(
        "Favoritos", back_populates="usuario")

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.name,
            # Incluye favoritos de forma simple, sin usar .serialize() completo
            "favoritos": [
                {
                    "pokemon_id": f.pokemon.id,
                    "pokemon_nombre": f.pokemon.name
                } for f in self.favoritos
            ]
        }


class Pokemon(db.Model):
    __tablename__ = "pokemon"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    favoritos: Mapped[list["Favoritos"]] = relationship(
        "Favoritos", back_populates="pokemon")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url
        }

# Son algo asi como las armas para capturar pokemon


class Pokeballs(db.Model):
    __tablename__ = "pokeballs"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    efectividad: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False)

    # favoritos: Mapped[list["Favoritos"]] = relationship(
    #     "Favoritos", back_populates="pokeballs")

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "efectividad": self.efectividad,
            "descripcion": self.descripcion
        }


class Favoritos(db.Model):
    __tablename__ = "favoritos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    # pokeballs_id: Mapped[int] = mapped_column(
    #     ForeignKey("pokeballs.id"), nullable=True)

    usuario: Mapped["User"] = relationship("User", back_populates="favoritos")
    pokemon: Mapped["Pokemon"] = relationship(
        "Pokemon", back_populates="favoritos")
    # pokeballs: Mapped["Pokeballs"] = relationship(
    #     "Pokeballs", back_populates="favoritos")

    def serialize(self):
        return {
            "favorito": self.pokemon.serialize(),
        }
