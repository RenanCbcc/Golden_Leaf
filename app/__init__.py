#!/usr/bin/python3
from flask import Flask
from flask_admin import Admin
from flask_bootstrap import Bootstrap
from flask_breadcrumbs import Breadcrumbs
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

bootstrap = Bootstrap()
breadcrumbs = Breadcrumbs()
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'blueprint_clerk.login'  # Function's name of route login from the blueprint.
login_manager.login_message_category = 'info'
admin = Admin(name='Golden Leaf', template_mode='bootstrap3')


def create_app(config_class):
    app = Flask(__name__)
    migrate.init_app(app, db)
    app.config.from_object(config_class)
    db.init_app(app)
    bootstrap.init_app(app)
    breadcrumbs.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    admin.init_app(app)

    from app.error.handler import blueprint_error
    app.register_blueprint(blueprint_error)

    from app.clerk.routes import blueprint_clerk
    app.register_blueprint(blueprint_clerk)

    from app.client.routes import blueprint_client
    app.register_blueprint(blueprint_client)

    from app.category.routes import blueprint_category
    app.register_blueprint(blueprint_category)

    from app.product.routes import blueprint_product
    app.register_blueprint(blueprint_product)

    from app.order.routes import blueprint_order
    app.register_blueprint(blueprint_order)

    from app.payment.routes import blueprint_payment
    app.register_blueprint(blueprint_payment)

    from app.main.routes import main
    app.register_blueprint(main)

    from app.api import api
    app.register_blueprint(api, url_prefix='/api')

    return app
