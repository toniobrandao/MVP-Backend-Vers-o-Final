from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import ItemModel
from sqlalchemy.exc import SQLAlchemyError

# módulo para ter requerir um JWT para obter acesso.
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.db import db
from schemas.schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("Items", "items", description="Operações nos itens")


@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        """Faz a busca de um item a partir do ID informado."""
        item = ItemModel.query.get_or_404(item_id)
        return item

    def delete(self, item_id):
        """Deleta um item a partir do ID informado."""
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted."}

    @blp.response(200, ItemSchema)
    @blp.arguments(ItemUpdateSchema)
    @jwt_required()
    def put(self, item_data, item_id):
        """Edita um item a partir de seu ID informado."""
        item = ItemModel.query.get_or_404(item_id)
        if item:
            if "quantity" in item_data:
                item.quantity = item_data["quantity"]
            if "name" in item_data:
                item.name = item_data["name"]
            if "category" in item_data:
                item.category = item_data["category"]
            if "is_packed" in item_data:
                item.is_packed = item_data["is_packed"]
        else:
            item = ItemModel(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        return item


@blp.route("/item")
class ItemList(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        """Faz a busca de todos os items cadastrados"""
        return ItemModel.query.all()

    # Só pode chamar o endpoint se enviar o JWT.
    @jwt_required()
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        """Adiciona um novo item à base de dados"""

        # Decode the JWT token to get the user ID if available
        user_id = get_jwt_identity()

        # Check if a user ID was found in the JWT
        if user_id is None:
            user_id = 0  # Set it to zero if no user ID was found

        # Create a new item with the user_id
        item = ItemModel(**item_data, user_id=user_id)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error ocurred while inserting the item.")
        return item


@blp.route("/items/<int:pack_id>")
class ItemDeletion(MethodView):
    @jwt_required()
    @blp.response(204)
    def delete(self, pack_id):
        """Deleta todos os itens para um determinado pack_id e user_id do JWT."""

        user_id = get_jwt_identity()

        # Check if a user ID was found in the JWT
        if user_id is None:
            abort(401, message="Authentication required.")

        # Use SQLAlchemy to delete items matching pack_id and user_id
        items_to_delete = ItemModel.query.filter_by(
            pack_id=pack_id, user_id=user_id).all()
        for item in items_to_delete:
            db.session.delete(item)

        db.session.commit()

        # Não retorna nada, pois o status code 204 no flask implica sem conteúdo para resposta.
        return
