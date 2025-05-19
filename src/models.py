from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey
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
            "name": self.name,
            "favoritos": [f.serialize() for f in self.favoritos]
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


class Favoritos(db.Model):
    __tablename__ = "favoritos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))

    usuario: Mapped["User"] = relationship("User", back_populates="favoritos")
    pokemon: Mapped["Pokemon"] = relationship(
        "Pokemon", back_populates="favoritos")

    def serialize(self):
        return {
            # para mostrar info completa del pokemon favorito
            "pokemon": self.pokemon.serialize()
        }
