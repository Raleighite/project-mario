from flask import Blueprint

web_bp = Blueprint('web', __name__)

from app.web import auth, main, tiles, courses  # noqa: E402, F401
