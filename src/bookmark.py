from flask import Blueprint, request, jsonify
from src.model import Bookmark, db
from src.constants.http_status_codes import *
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
from flasgger import swag_from

bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")

# this route creates a bookmark and also fetches all bookmark
@bookmarks.post("/")
@jwt_required()
@swag_from("./docs/bookmarks/create_bookmark.yml", validation= True)
def create_bookmarks():
    current_user = get_jwt_identity()
   
    body = request.json["body"]
    url = request.json["url"]

    # check if the required field were provided
    if not body or not url:
        return jsonify({"error": "All fields are required"}), HTTP_400_BAD_REQUEST
    
    # check if the provided url was valid
    if not validators.url(url):
        return jsonify({"error": "Valid url required"}), HTTP_400_BAD_REQUEST
    
    # check if ur already exist
    if Bookmark.query.filter_by(url=url).first():
        return jsonify({"error": "url already exist"}), HTTP_409_CONFLICT
    
    # create the new bookmark object and store in db
    bookmark = Bookmark(body = body, url = url, user_id=current_user)

    db.session.add(bookmark)
    db.session.commit()

    return jsonify({"message":"bookmark created"}), HTTP_201_CREATED

@bookmarks.get('/')
@jwt_required()
@swag_from('./docs/bookmarks/get_bookmarks.yml', validation= True)
def get_all_bookmarks():
    current_user = get_jwt_identity()

    # the mothod here is a GET request so we query the db to send all users
    page = request.args.get('page',1, type= int)
    per_page = request.args.get('per_page',5 , type= int)

    bookmarks = Bookmark.query.filter_by(user_id= current_user).paginate(page=page, per_page=per_page)
    all_bookmarks = []

    for bookmark in bookmarks.items:
        all_bookmarks.append({
            "id": bookmark.id,
            "body": bookmark.body,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visited": bookmark.visited,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at
        })

    meta = {
        "page": bookmarks.page,
        "pages": bookmarks.pages,
        "has_next": bookmarks.has_next,
        "has_prev": bookmarks.has_prev,
        "next_page": bookmarks.next_num,
        "prev_page": bookmarks.prev_num,
        "total_count": bookmarks.total
    }
    return jsonify({
        "bookmarks": all_bookmarks,
        "meta": meta
    }), HTTP_200_OK

# this route fetches a single bookmark
@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id= user_id, id= id).first()

    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND
    
    return jsonify({
        "id": bookmark.id,
        "body": bookmark.body,
        "url": bookmark.url,
        "short_url": bookmark.short_url,
        "visited": bookmark.visited,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at
    }),HTTP_200_OK

# this route updates a bookmark
# @bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
@swag_from('./docs/bookmarks/update_bookmark.yml')
def update_bookmark(id):
    user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id= user_id, id= id).first()

    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND
    
    body = request.json["body"]
    url = request.json["url"]

    if not body or not url:
        return jsonify({"error": "All fields are rewuired"}), HTTP_400_BAD_REQUEST
    
    # check if new url already exist

    found_url = Bookmark.query.filter_by(url= url, user_id= user_id).first()

    if not validators.url(url):
        return jsonify({"error": "Enter a valid url"}), HTTP_400_BAD_REQUEST
    
    if found_url:
        return jsonify({"message": "Url already exist"}), HTTP_409_CONFLICT

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return jsonify({
        "id": bookmark.id,
        "body": bookmark.body,
        "url": bookmark.url,
        "short_url": bookmark.short_url,
        "visited": bookmark.visited,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at
    }), HTTP_200_OK


# this route deletes a particular bookmark
@bookmarks.delete("/<int:id>")
@jwt_required()
@swag_from('./docs/bookmarks/delete_bookmark.yml', validation=True)
def delete_bookmark(id):
    user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id= user_id, id= id).first()

    if not bookmark:
        return jsonify({"message": "Bookmark not found"}), HTTP_404_NOT_FOUND
    
    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT

@bookmarks.get("/stats")
@jwt_required()
@swag_from('./docs/bookmarks/stats.yml')
def handle_get_stats():
    user_id = get_jwt_identity()
    items = Bookmark.query.filter_by(user_id = user_id).all()

    data = []

    for item in items:
        new_item = {
            "id": item.id,
            "visited": item.visited,
            "short_url": item.short_url,
            "url": item.url
        }

        data.append(new_item)

    return jsonify({"stats": data}), HTTP_200_OK