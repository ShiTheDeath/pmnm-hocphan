import os

from flask import Flask, render_template, request, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from . import models  # noqa: F401  (để migration thấy các model)
    from .admin import bp as admin_bp
    from .shop import bp as shop_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.template_filter("vnd")
    def vnd(value):
        return f"{int(value or 0):,}".replace(",", ".") + " đ"

    @app.template_filter("num")
    def num(value):
        return f"{int(value or 0):,}".replace(",", ".")

    @app.template_filter("dt")
    def dt(value, fmt="%d/%m/%Y %H:%M"):
        return value.strftime(fmt) if value else ""

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        ctx = {"cart_count": sum(cart.values())}
        if request.blueprint == "admin":
            from sqlalchemy import func

            ctx["pending_count"] = (
                db.session.query(func.count(models.Order.id))
                .filter(models.Order.status == "pending")
                .scalar()
            )
        ctx["STATUS_LABELS"] = models.STATUS_LABELS
        return ctx

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    from .seed import register_cli

    register_cli(app)
    return app