import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import datetime


class News(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'news'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    color = sqlalchemy.Column(sqlalchemy.String)
    title = sqlalchemy.Column(sqlalchemy.String)
    text = sqlalchemy.Column(sqlalchemy.String)
    creator = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("users.id"))
    date_of_create = sqlalchemy.Column(sqlalchemy.String,  default=datetime.datetime.now().date())
    category = sqlalchemy.Column(sqlalchemy.String)
    user = orm.relation('User')
