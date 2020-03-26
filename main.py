from flask import Flask, render_template, redirect, request, abort
from data import db_session, news, users, accounts
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(users.User).get(user_id)


@app.route("/")
def index():
    return render_template('base.html', title='Todoroki')


@app.route("/forum")
def forum():
    return render_template('forum.html', title='Todoroki | Форум')


@app.route('/market')
def market():
    return render_template('market.html', title='Todoroki | Маркет')


def main():
    db_session.global_init('db/database.sqlite')
    app.run(port=88, host='127.0.0.1')


if __name__ == '__main__':
    main()
