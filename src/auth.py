from flask import Blueprint, request, jsonify
from src.constants.http_status_codes import *
import validators
from werkzeug.security import generate_password_hash, check_password_hash
from src.model import User, db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post("/login")
@swag_from("./docs/auth/login.yml")
def login():
    email = request.json["email"]
    password = request.json["password"]

    # check if password and email was provided
    if not password or not email:
        return jsonify({"error": "All fields are required"}), HTTP_400_BAD_REQUEST
    
    # check if email exist 
    user = User.query.filter_by(email = email).first()
    if user:
        # check if password provided was valid
        verified_user = check_password_hash(user.password, password)
        if verified_user:
            # create an access and refresh token
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            # send a json response with the access and refresh token
            return jsonify({"access_token": access_token,
                            "refresh_token": refresh_token,
                            "user": {"email": user.email,
                                     "username": user.username}
                            }), HTTP_200_OK
    return jsonify({"error": "Wrong credentials"}), HTTP_400_BAD_REQUEST


@auth.post("/register")
@swag_from('./docs/auth/register.yml')
def register():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]

    # check password length
    if len(password) < 6:
        return jsonify({"error": "Password too short"}), HTTP_400_BAD_REQUEST
   
    # check username length
    if len(username)< 3:
        return jsonify({"error": "Username too short"}), HTTP_400_BAD_REQUEST
    
    # check if username is alpha numeric and has no spaces
    if not username.isalnum() or " " in username:
        return jsonify({"error": "Username must be alphaNumeric and spaces are not allowed"}), HTTP_400_BAD_REQUEST

    # check if email provided is valid
    if not validators.email(email):
        return jsonify({"error": "Only valid email addresses are allowed"}), HTTP_400_BAD_REQUEST
    
    # check if username already exist 
    if User.query.filter_by(username = username).first() is not None:
        return jsonify({"error": "Username already exist"}), HTTP_409_CONFLICT
    
    # check if email already exist
    if User.query.filter_by(email = email).first() is not None:
        return jsonify({"error": "email already exist"}), HTTP_409_CONFLICT
    
    # generate password hash
    hash_pwd = generate_password_hash(password, method="pbkdf2", salt_length=10)
    
    # add user to database
    user = User(username= username, email = email, password = hash_pwd)

    db.session.add(user)
    db.session.commit()

    # return success message
    return jsonify({
        "message": "User created",
        "user": {
            "username": username,
            "email": email
        }
    }),HTTP_201_CREATED

@auth.get("/token/refresh")
@jwt_required(refresh=True)
def get_token_from_refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token})


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        "username": user.username,
        "email": user.email
    }), 200