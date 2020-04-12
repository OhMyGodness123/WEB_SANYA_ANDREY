from flask_restful import reqparse, abort, Api, Resource
from data import db_session, news
from flask import jsonify


def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    new = session.query(news.News).get(news_id)
    if not new:
        abort(404, message=f"News {news_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        new = session.query(news.News).get(news_id)
        return jsonify({'news': new.to_dict(
            only=('id', 'text', 'creator'))})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        new = session.query(news.News).get(news_id)
        session.delete(new)
        session.commit()
        return jsonify({'success': 'OK'})


parser = reqparse.RequestParser()
parser.add_argument('id', required=True)
parser.add_argument('color', required=True)
parser.add_argument('title', required=True)
parser.add_argument('text', required=True)
parser.add_argument('creator', required=True)
parser.add_argument('date_of_create', required=True)
parser.add_argument('category', required=True)


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        new = session.query(news.News).all()
        return jsonify({'news': [item.to_dict(
            only=('id', 'text', 'creator')) for item in new]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        new = news.News(
            id=args['id'],
            color=args['color'],
            title=args['title'],
            text=args['text'],
            creator=args['creator'],
            date_of_create=args['date_of_create'],
            category=args['category']
        )
        session.add(new)
        session.commit()
        return jsonify({'success': 'OK'})
