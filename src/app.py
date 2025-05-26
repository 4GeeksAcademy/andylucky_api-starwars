
"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from sqlalchemy import select
from models import db, Pokemon, Pokeballs, User, Favoritos
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


# GET: Muestra todos los pokemon que hay
@app.route("/pokemon", methods=["GET"])
def get_pokemon():
    stmt = select(Pokemon)
    # Esto te da una lista de instancias de Pokemon
    pokemons = db.session.execute(stmt).scalars().all()
    return jsonify([p.serialize() for p in pokemons]), 200


@app.route("/users", methods=["GET"])
def get_usuario():
    stmt = select(User)
    users = db.session.execute(stmt).scalars().all()
    return jsonify([user.serialize() for user in users]), 200


@app.route("/users/favoritos", methods=["GET"])
def get_favorito():
    stmt = select(Favoritos)
    favoritos = db.session.execute(stmt).scalars().all()

    pokeballs_unicos = {}
    # un diccionario no permite claves repetidas, asi que
    # si encuentra una la sobreescribe a la que habia
    for fav in favoritos:
        if fav.pokemon.id in pokeballs_unicos:
            # Si ya está, aumentamos la cantidad
            pokeballs_unicos[fav.pokemon.id]["cantidad_veces_favorito"] += 1
        else:
            # Si no está, la inicializamos con cantidad 1
            pokeballs_unicos[fav.pokemon.id] = {
                "favorito_id": fav.pokemon.id,
                "pokemon_nombre": fav.pokemon.name,
                "cantidad_veces_favorito": 1
            }
    return jsonify(list(pokeballs_unicos.values())), 200


@app.route("/pokeballs", methods=["GET"])
def get_pokeballs():
    stmt = select(Pokeballs)
    pokeballs = db.session.execute(stmt).scalars().all()
    return jsonify([p.serialize() for p in pokeballs]), 200


@app.route("/favoritos/<int:id>", methods=["GET"])
def get_onefavorito(id):
    stmt = select(Favoritos).where(Favoritos.id == id)
    # Esto te da una lista de instancias de Pokemon
    favorito = db.session.execute(stmt).scalar_one_or_none()
    if favorito is None:
        return jsonify({"error": "Pokemon not found"}), 404
    return jsonify(favorito.serialize()), 200


# GET ONE: Muestra un pokemon por su id
@app.route("/pokemon/<int:id>", methods=["GET"])
def get_pokemonone(id):
    stmt = select(Pokemon).where(Pokemon.id == id)
    # Esto te da una lista de instancias de Pokemon
    pokemons = db.session.execute(stmt).scalar_one_or_none()
    if pokemons is None:
        return jsonify({"error": "Pokemon not found"}), 404
    return jsonify(pokemons.serialize()), 200


# para crear en postmat un nuevo user tiene que ir con algun favorito [
#   {
#     "name": "pascualin",
#     "favoritos": [4]
#   }
#
@app.route("/createusers", methods=["POST"])
def create_users():
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({"error": "Missing or invalid data, expected a list"}), 400

    nuevos_usuarios = []

    for item in data:
        if "name" not in item or "favoritos" not in item:
            return jsonify({"error": "Missing name or favoritos in one of the users"}), 400

        new_user = User(name=item["name"])
        db.session.add(new_user)
        db.session.flush()  # asigna ID a new_user para favoritos

        favoritos_a_agregar = []
        for poke_id in item["favoritos"]:
            favorito = Favoritos(user_id=new_user.id, pokemon_id=poke_id)
            favoritos_a_agregar.append(favorito)

        nuevos_usuarios.append(new_user)
        db.session.add_all(favoritos_a_agregar)

    db.session.commit()

    return jsonify([usuario.serialize() for usuario in nuevos_usuarios]), 201


# POST: crea un nuevo pokemon favorito para un usuario dado
@app.route("/favorito/pokemon/<int:id>", methods=["POST"])
def create_poke_favorito(id):
    data = request.get_json()
    if not data or "name" not in data or "url" not in data:
        return jsonify({"error": "Missing data"}), 400
    # Buscar usuario por id
    stmt = select(User).where(User.id == id)
    usuario = db.session.execute(stmt).scalar_one_or_none()
    if usuario is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    nombre_nuevo = data["name"].strip().lower()

    # Comprobar si usuario ya tiene un favorito con ese nombre
    existe_favorito = any(
        favorito.pokemon.name.strip().lower() == nombre_nuevo
        for favorito in usuario.favoritos
    )
    if existe_favorito:
        return jsonify({"error": "El usuario ya tiene un favorito con ese nombre"}), 409

    # Crear nuevo Pokémon
    new_pokemon = Pokemon(
        name=data["name"],
        url=data["url"]
    )
    db.session.add(new_pokemon)
    db.session.flush()  # para asignar ID al nuevo Pokémon antes de crear Favoritos

    # Crear nueva relación Favoritos entre usuario y el nuevo Pokémon
    nuevo_favorito = Favoritos(
        usuario=usuario,
        pokemon=new_pokemon
    )
    db.session.add(nuevo_favorito)

    # Guardar cambios en la base de datos
    db.session.commit()

    # Devolver usuario serializado con su lista de favoritos actualizada
    return jsonify({"usuario": usuario.serialize()}), 201


# POST: crea un nuevo pokemonballs favorito para un usuario dado
@app.route("/favorito/pokeballs/<int:id>", methods=["POST"])
def create_pokeballs_favorito(id):
    data = request.get_json()
    if not data or "nombre" not in data or "descripcion" not in data or "efectividad" not in data:
        return jsonify({"error": "Missing data"}), 400
    # Buscar usuario por id
    stmt = select(User).where(User.id == id)
    usuario = db.session.execute(stmt).scalar_one_or_none()
    if usuario is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    nombre_nuevo = data["nombre"].strip().lower()

    # Comprobar si usuario ya tiene un favorito con ese nombre
    existe_favorito = any(
        favorito.pokemonballs.name.strip().lower() == nombre_nuevo
        for favorito in usuario.favoritos
    )
    if existe_favorito:
        return jsonify({"error": "El usuario ya tiene un favorito con ese nombre"}), 409

    # Crear nuevo Pokémon
    new_pokeballs = Pokeballs(
        nombre=data["nombre"],
        efectividad=data["efectividad"],
        descripcion=data["descripcion"]
    )
    db.session.add(new_pokeballs)
    db.session.flush()  # para asignar ID al nuevo Pokémon antes de crear Favoritos

    # Crear nueva relación Favoritos entre usuario y el nuevo Pokémon
    nuevo_favorito_pokeballs = Favoritos(
        usuario=usuario,
        pokeballs=new_pokeballs
    )
    db.session.add(nuevo_favorito_pokeballs)

    # Guardar cambios en la base de datos
    db.session.commit()

    # Devolver usuario serializado con su lista de favoritos actualizada
    return jsonify({"usuario": usuario.serialize()}), 201


# POST: crea un nuevo pokemon favorito para un usuario dado
@app.route("/favorito/pokeballs", methods=["POST"])
def create_pokeball_favorito():
    data = request.get_json()
    if not data or "nombre" not in data or "efectividad" not in data or "descripcion" not in data:
        return jsonify({"error": "Missing data"}), 400

    new_pokeball = Pokeballs(
        nombre=data["nombre"],
        # Por si mandas 1.0, convertir a entero
        efectividad=int(data["efectividad"]),
        descripcion=data["descripcion"]
    )
    db.session.add(new_pokeball)
    db.session.commit()

    return jsonify(new_pokeball.serialize()), 201


# PUT: Actualizamos un pokemon por el id
@app.route("/pokemonput/<int:id>", methods=["PUT"])
def update_pokemon(id):
    # extraemos la informacion del body
    data = request.get_json()
    # data= request.json
    # buscamos el pokemon porque vamos a editar
    stmt = select(Pokemon).where(Pokemon.id == id)
    pokemon = db.session.execute(stmt).scalar_one_or_none()
    # si no encontramos Pokemon devolvemos que no existe
    if pokemon is None:
        return jsonify({"error": "Pokemon not found"}), 404
    # modificamos las propiedades del objeto Pokemon
    # le ponemos el name que recibimos o si no recibimos name, mantenemos el que estaba
    pokemon.name = data.get("name", pokemon.name)
    pokemon.url = data.get("url", pokemon.url)
    # almacenamos las cambios
    db.session.commit()
    return jsonify(pokemon.serialize()), 200


# DELETE: Elimina un pokemon por el id
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_pokemon(id):
    # seleccionamos usuario a eliminar
    stmt = select(Pokemon).where(Pokemon.id == id)
    poke = db.session.execute(stmt).scalar_one_or_none()
    if poke is None:
        return jsonify({"error": "poke not found"}), 404
    # eliminamos Pokemon
    db.session.delete(poke)
    # almacenamos cambios
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


# DELETE: Elimina un pokemon-favorito por el id
@app.route("/favorito/pokemon/<int:id>", methods=["DELETE"])
def delete_pokemonfavorito(id):
    # seleccionamos favorito a eliminar
    stmt = select(Favoritos).where(Favoritos.id == id)
    favorito = db.session.execute(stmt).scalar_one_or_none()
    if favorito is None:
        return jsonify({"error": "favorito not found"}), 404
    # eliminamos favorito
    db.session.delete(favorito)
    # almacenamoss cambios
    db.session.commit()
    return jsonify({"message": "favorito deleted"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
