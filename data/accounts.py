import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Accounts(SqlAlchemyBase, UserMixin, SerializerMixin):  # класс товаров в маркете
    __tablename__ = 'accounts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    title = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.String)
    count = sqlalchemy.Column(sqlalchemy.Integer)
    vk_silka = sqlalchemy.Column(sqlalchemy.String)
    user_name = sqlalchemy.Column(sqlalchemy.String)

