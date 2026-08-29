import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # The JSON API is authenticated via the Flask-Login session cookie (which is
    # itself SameSite-protected) rather than form-based CSRF tokens, since all
    # calls are same-origin fetch() requests from our own JS.
    csrf.exempt(api_bp)

    with app.app_context():
        db.create_all()
        from app.seed_data import seed_if_empty
        seed_if_empty()

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    return app
