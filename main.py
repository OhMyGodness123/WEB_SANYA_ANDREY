from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from data import db_session, news, users

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    sessions = db_session.create_session()
    return sessions.query(users.User).get(user_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


class RegisterForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Содержание')
    is_private = BooleanField('Приватность')
    submit = SubmitField('Применить')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = news.News()
        new.title = form.title.data
        new.content = form.content.data
        new.is_private = form.is_private.data
        current_user.news.append(new)
        sessions.merge(current_user)
        sessions.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.id == id,
                                           news.News.user == current_user).first()
    if new:
        sessions.delete(new)
        sessions.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            form.title.data = new.title
            form.content.data = new.content
            form.is_private.data = new.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            new.title = form.title.data
            new.content = form.content.data
            new.is_private = form.is_private.data
            sessions.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(users.User).filter(users.User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = users.User(
            nickname=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


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
    db_session.global_init("db/blogs.sqlite")
    app.run(port=2111, host='127.0.0.1')


if __name__ == '__main__':
    main()
