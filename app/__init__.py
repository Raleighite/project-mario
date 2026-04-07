from flask import Flask, redirect, url_for
from config import config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User, Tile, Course, CourseTile  # noqa: F401

    from app.web import web_bp
    app.register_blueprint(web_bp)

    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    csrf.exempt(api_bp)

    from app.cli import register_commands
    register_commands(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('web.login'))

    return app
