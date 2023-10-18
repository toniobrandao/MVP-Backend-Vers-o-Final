from models.db import db
from flask.views import MethodView
from flask_smorest import Blueprint, abort

# biblioteca para usar o hash nas senhas dos usuários.
from passlib.hash import pbkdf2_sha256


# Para criar um JWT para ser enviado ao cliente.
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt

from models import UserModel
from schemas.schemas import UserSchema
from blocklist import BLOCKLIST
from function_utils import generate_random_password, send_email


blp = Blueprint("Users", "users", description="Operações nos users")


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        """Faz login do usuário e fornece um JWT (access token)."""

        # Checando se o usuário e senha estão corretos.
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]).first()

        # checa se as duas senhas, ao aplicado encriptação hash nelas, são as mesmas.
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token, "username": user_data["username"]}

        abort(401, message="Invalid Credentials")


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        """Faz logout do usuário e joga fora o JWT(access token) utilizado no login."""

        # jti é o ID do JWT.
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        """Adiciona um novo usuário e senha com hash à base de dados."""

        # Checando se o nome de usuário é único.
        # .first() por que, se existe somente uma linha, ja é o suficiente para ter um nome de usuários
        # no banco de dados igual ao solicitado no post request.
        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="A user with that username already exists.")

        if UserModel.query.filter(UserModel.email == user_data["email"]).first():
            abort(409, message="A user with that email already exists. ")

        user = UserModel(username=user_data["username"],
                         email=user_data["email"],
                         password=pbkdf2_sha256.hash(user_data["password"]))
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully.", "code": 201}, 201


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        """O cliente fornecendo o token de refresh, recebe de volta um novo JWT,
          para caso o JWT atual estiver expirado."""
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    @jwt_required()
    def delete(self, user_id):
        """Deleta o usuário a partir do ID informado."""

        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted.", "code": 200}, 200


@blp.route("/user/password_recovery/<string:user_email>")
class UpdateUserPassword(MethodView):
    @blp.response(200, UserSchema)
    def put(self, user_email):
        """Envia um e-mail para o usuário, com a nova senha."""
        user = UserModel.query.filter_by(email=user_email).first()

        if not user:
            return {"message": "User not found"}, 404

        new_password = generate_random_password()

        # Update the user's password
        user.password = pbkdf2_sha256.hash(new_password)

        # Commit the changes to the database
        db.session.commit()

        subject = "Nova senha gerada com sucesso!"
        body = f"Nome de usuário: {user.username} \nSua nova senha é: {new_password}"
        send_email(subject, body, user_email)

        return {"message": "Password updated successfully"}
