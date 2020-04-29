import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Book(SqlAlchemyBase, UserMixin, SerializerMixin):  # класс отзывов из вк бота
    __tablename__ = 'complaint_book'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    vk_id = sqlalchemy.Column(sqlalchemy.Integer)
    type_of_message = sqlalchemy.Column(sqlalchemy.String)
    comment_text = sqlalchemy.Column(sqlalchemy.String)
