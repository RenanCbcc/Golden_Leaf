import decimal
from abc import ABCMeta
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship, backref
from werkzeug.routing import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager, db
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
import enum


@login_manager.user_loader
def load_user(id):
    return Clerk.query.get(id)


class Status(enum.Enum):
    PAGO = "Pago"
    PENDENTE = "Pendente"


class User(db.Model):
    """
    Using Concrete Table Inheritance Mapping.
    """
    __metaclass__ = ABCMeta
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    phone_number = db.Column(db.String(9), nullable=False)

    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number


class Client(User):
    __tablename__ = 'clients'
    __mapper_args__ = {'concrete': True}
    identification = db.Column(db.String(11), unique=True)
    notifiable = db.Column(db.Boolean)
    address_id = db.Column(db.Integer, ForeignKey('addresses.id'))
    address = db.relationship("Address", back_populates="dweller", lazy=False)
    status = db.Column(db.Boolean)
    orders = relationship("Order", back_populates="client")

    def __init__(self, name, phone_number, identification, address, notifiable, status=True):
        super().__init__(name, phone_number)
        self.identification = identification
        self.notifiable = notifiable
        self.address = address
        self.status = status

    def to_json(self):
        json_client = {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'identification': self.identification,
            'address': url_for('api.get_client_address', id=self.id),
            'notifiable': self.notifiable,
            'status': self.status
        }
        return json_client

    @staticmethod
    def from_json(content):
        if content['name'] == "" or content['phone_number'] == "" or content['identification'] == "":
            raise ValidationError("Cliente não pode ter valores nulos")
        client = Client(content.get('name'), content.get('phone_number'), content.get('identification'),
                        Address.from_json(content['address']), content.get('notifiable'))
        return client

    def __eq__(self, other):
        return self.identification == other.identification

    def __repr__(self):
        return '<Cliente %r %r %r %r>' % (self.name, self.identification, self.phone_number, self.status)


class Clerk(User, UserMixin):
    __tablename__ = 'clerks'
    image_file = db.Column(db.String(24), default='default.jpg')
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    orders = relationship("Order", back_populates="clerk")

    __mapper_args__ = {
        'concrete': True
    }

    def __init__(self, name, phone_number, email, password):
        super().__init__(name, phone_number)
        self.email = email
        self.password = password

    def get_token(self, expires_sec=1800):
        """
        The token is an encrypted version of a dictionary that has the id of the user
        :param expires_sec:
        :return:
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'clerk_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            clerk_id = s.loads(token)['clerk_id']
        except:
            return None
        return Clerk.query.get(clerk_id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Atendente %r %r>' % (self.name, self.email)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Enum(Status), default=Status.PENDENTE)

    client_id = db.Column(db.Integer, ForeignKey('clients.id'))
    client = relationship("Client", back_populates="orders")

    clerk_id = db.Column(db.Integer, ForeignKey('clerks.id'))
    clerk = relationship("Clerk", back_populates="orders")

    def __init__(self, date, client, clerk, items):
        self.date = date
        self.client = client
        self.clerk = clerk
        self.items = items

    def __repr__(self):
        return '<Pedido %r %r %r >' % (self.date, self.client.name, self.clerk.name)


class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(64), nullable=False)
    detail = db.Column(db.String(64))
    zip_code = db.Column(db.String(6), nullable=False)
    dweller = relationship("Client", uselist=False, back_populates="address")

    def __init__(self, street, detail, zip_code):
        self.street = street
        self.detail = detail
        self.zip_code = zip_code

    def to_json(self):
        json_address = {
            'id': self.id,
            'street': self.street,
            'detail': self.detail,
            'zip_code': self.zip_code,

        }
        return json_address

    @staticmethod
    def from_json(content):
        if content['street'] == "" or content['address_detail'] == "" or content['zip_code'] == "":
            raise ValidationError("Endereço não pode ter valores nulos")
        address = Address(content.get('street'), content.get('address_detail'), content.get('zip_code'))
        return address

    def __str__(self):
        return "Rua: {}, {}".format(self.street, self.detail)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(64))
    image_file = db.Column(db.String(32), default='default.jpg')
    unit_cost = db.Column(db.Numeric(6, 2), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False)
    code = db.Column(db.String(13), unique=True, nullable=False)
    category_id = db.Column(db.Integer, ForeignKey('categories.id'), nullable=False)

    __table_args__ = (CheckConstraint(unit_cost >= 0.00, name='unit_cost_positive'),)

    def __init__(self, category, brand, description, unit_cost, code, is_available=True):
        self.category = category  # This field is 'virtual' and was declared in Category as a backref
        self.brand = brand
        self.description = description
        self.unit_cost = unit_cost
        self.is_available = is_available
        self.code = code

    def to_json(self):
        json_product = {
            'id': self.id,
            'brand': self.brand,
            'description': self.description,
            'unit_cost': str(self.unit_cost),
            'is_available': self.is_available,
            'code': self.code
        }
        return json_product

    @staticmethod
    def from_json(json_product):

        brand = json_product.get('brand')
        description = json_product.get('name')
        unit_cost = decimal.Decimal(json_product.get('unit_cost'))
        code = json_product.get('code')

        if brand is None or brand == '':
            raise ValidationError('Produto tem com marca inválida')
        if description is None or description == '':
            raise ValidationError('Produto tem com descriçao inválida')
        if code is None or len(code) is not 13:
            raise ValidationError('Código de produto inválido')
        if unit_cost is None or unit_cost <= 0:
            raise ValidationError('Produto co preço inválido')

        return Product(brand, description, unit_cost, code)

    def __eq__(self, other):
        return self.code == other.code

    def __repr__(self):
        return '<Product %r %r %r %r>' % (self.brand, self.description, self.unit_cost, self.is_available)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), index=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

    def __init__(self, title):
        self.title = title

    def to_json(self):
        json_product = {
            'id': self.id,
            'title': self.title
        }
        return json_product

    @staticmethod
    def from_json(json_product):
        title = json_product.get('title')

        if title is None or title == '':
            raise ValidationError('Categoria tem com título inválido')

        return Category(title)

    def __repr__(self):
        return '<Category %r>' % self.title


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, ForeignKey('products.id'), nullable=False)
    order_id = db.Column(db.Integer, ForeignKey('orders.id'), nullable=False)
    quantity = db.Column(db.Numeric(5, 2))
    extended_cost = db.Column(db.Numeric(12, 2))

    order = db.relationship("Order", backref=backref('items', order_by=order_id))

    def __init__(self, product_id, demand_id, quantity):
        self.demand_id = demand_id
        self.product_id = product_id
        self.quantity = quantity

    def __repr__(self):
        return '<Item %r Quantidade %r>' % (self.product.description, self.quantity)
