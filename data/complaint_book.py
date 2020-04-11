import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
import datetime


class Book(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'complaint_book'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    vk_id = sqlalchemy.Column(sqlalchemy.Integer)
    type_of_message = sqlalchemy.Column(sqlalchemy.String)
    comment_text = sqlalchemy.Column(sqlalchemy.String)
