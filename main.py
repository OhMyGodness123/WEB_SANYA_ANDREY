from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, \
    SelectField
from wtforms.validators import DataRequired
from data import db_session, news, users
import random
import json
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class ForumForm(FlaskForm):
    message = TextAreaField('Введите своё сообщение:', validators=[DataRequired()])
    submit = SubmitField('Отправить')


class NewsForm(FlaskForm):
    title = StringField('Заголовок:', validators=[DataRequired()])
    text = TextAreaField('Содержание:')
    color = StringField('Цвет новости: #')
    category = SelectField('Категория',
                           choices=[('Новости', 'Новости'), ('Софт', 'Софт'), ('Халява', 'Халява'),
                                    ('Обсуждение игр', 'Обсуждение игр')])
    submit = SubmitField('Создать')


class SettingsForm(FlaskForm):
    email = StringField('Почта')
    old_pass = PasswordField('Старый пароль', validators=[DataRequired()])
    new_pass = PasswordField('Новый пароль')
    new_pass_again = PasswordField('Подтвердите новый пароль')
    submit = SubmitField('Сохранить')


@app.route('/logout')
@login_required
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
        new.text = form.text.data.replace('\n', '<br />&nbsp;&nbsp;&nbsp;')
        new.creator = current_user.nickname
        new.color = form.color.data
        new.category = form.category.data
        current_user.news.append(new)
        sessions.merge(current_user)
        sessions.commit()

        with open('forum.json', 'r') as jfr:
            jf_file = json.load(jfr)

        with open('forum.json', 'w') as jf:
            jf_target = jf_file["topics"]
            user_info = {"messages": [
                {"text": form.text.data.replace('\n', '<br />&nbsp;&nbsp;&nbsp;'),
                 "author": current_user.nickname}]}
            jf_target.append(user_info)
            json.dump(jf_file, jf, indent=4)

        return redirect('/')
    return render_template('add_news.html', title='Добавление новости', form=form,
                           nickname=current_user.nickname, image=current_user.avatar)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.id == id,
                                           news.News.user == current_user).first()
    if new:
        sessions.delete(new)
        sessions.commit()
        with open('forum.json', 'r') as fp:
            jsondata = json.load(fp)
        jsondata = {
            'topics': [obj for obj in jsondata["topics"] if
                       jsondata["topics"].index(obj) != id - 1]}
        with open('forum.json', 'w') as jf:
            json.dump(jsondata, jf, indent=4)
    else:
        abort(404)
    return redirect('/')


@app.route('/change_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            form.title.data = new.title
            form.text.data = new.text.replace('<br />&nbsp;&nbsp;&nbsp;', '')
            form.category.data = new.category
            form.color.data = new.color
        else:
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            new.title = form.title.data
            new.text = form.text.data
            new.color = form.color.data
            new.category = form.category.data
            sessions.commit()

            with open('forum.json') as f:
                data = json.load(f)
            data["topics"][id - 1]["messages"][0]["text"] = form.text.data.replace('\n',
                                                                                   '<br />&nbsp;&nbsp;&nbsp;')
            with open('forum.json', 'w') as f:
                json.dump(data, indent=4, fp=f)

            return redirect('/')
        else:
            abort(404)
    return render_template('add_news.html', form=form,
                           nickname=current_user.nickname, image=current_user.avatar,
                           title='Редактирование')


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
        try:
            file = request.files['file']
            path = app.config['UPLOAD_FOLDER'] + file.filename
            file.save(path)
        except PermissionError:
            img = random.choice(['avatar1.png', 'avatar2.png', 'avatar3.png', 'avatar4.png',
                                 'avatar5.png', 'avatar6.png', 'avatar7.png'])
            path = f"/static/img/{img}"
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.email == form.email.data).first() or session.query(users.User).filter(
            users.User.nickname == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = users.User(
            nickname=form.name.data,
            email=form.email.data,
            avatar=path
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/")
def index():
    session = db_session.create_session()
    new = session.query(news.News).all()
    new.reverse()
    if current_user.is_authenticated:
        return render_template('forum.html', title='Todoroki', nickname=current_user.nickname,
                               image=current_user.avatar, news=new)
    return render_template('forum.html', title='Todoroki', news=new)


@app.route("/discussion/<int:news_id>", methods=['GET', 'POST'])
def discussion(news_id):
    forum = ForumForm()
    session = db_session.create_session()
    new = session.query(news.News).filter(news.News.id == news_id).first()
    messages = forum.message.data
    if forum.validate_on_submit():
        write_to_json(messages, current_user.nickname, news_id)
    with open('forum.json', 'r') as jfr:
        info = json.load(jfr)["topics"][news_id - 1]["messages"]
    if current_user.is_authenticated:
        return render_template('discussion.html', nickname=current_user.nickname,
                               image=current_user.avatar, messages=info, form=forum,
                               title=new.title, category=new.category)
    return render_template('discussion.html', messages=info, form=forum, title=new.title,
                           category=new.category)


def write_to_json(text, author, news_id):
    with open('forum.json', 'r') as jfr:
        jf_file = json.load(jfr)
    with open('forum.json', 'w') as jf:
        jf_target = jf_file["topics"][news_id - 1]["messages"]
        user_info = {"text": text, "author": author}
        jf_target.append(user_info)
        json.dump(jf_file, jf, indent=4)


@app.route("/<category>")
def sorted_news(category):
    session = db_session.create_session()
    if category == 'only_games':
        new = session.query(news.News).filter(news.News.category == 'Обсуждение игр').all()
    elif category == 'only_soft':
        new = session.query(news.News).filter(news.News.category == 'Софт').all()
    elif category == 'only_halyava':
        new = session.query(news.News).filter(news.News.category == 'Халява').all()
    else:
        new = session.query(news.News).filter(news.News.category == 'Новости').all()
    new.reverse()
    if current_user.is_authenticated:
        return render_template('forum.html', title='Todoroki', nickname=current_user.nickname,
                               image=current_user.avatar, news=new)
    return render_template('forum.html', title='Todoroki', news=new)


@app.route('/market')
def market():
    if current_user.is_authenticated:
        return render_template('market.html', title='Todoroki | Маркет',
                               nickname=current_user.nickname,
                               image=current_user.avatar)
    return render_template('market.html', title='Todoroki | Маркет')


@app.route('/profile')
def my_profile():
    return render_template('my_profile.html', title='Todoroki | Мой профиль',
                           nickname=current_user.nickname, image=current_user.avatar,
                           mail=current_user.email, created_date=current_user.date_of_registration)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.id == current_user.id).first()
        if user.check_password(form.old_pass.data):
            if form.new_pass.data == form.new_pass_again.data and form.new_pass.data != '':
                if user:
                    user.set_password(form.new_pass.data)
                    session.commit()
                    return redirect('/')
                else:
                    abort(404)
            elif current_user.email != form.email.data:
                user.email = form.email.data
                session.commit()
                return redirect('/')
            else:
                return render_template('settings.html', title='Todoroki | Настройки',
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       form=form, message='Пароли не совпадают')
        else:
            return render_template('settings.html', title='Todoroki | Настройки',
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   form=form, message='Неверный пароль')
    return render_template('settings.html', title='Todoroki | Настройки',
                           nickname=current_user.nickname, image=current_user.avatar, form=form)


@app.route('/about')
def about():
    map_request = "https://static-maps.yandex.ru/1.x/" \
                  "?ll=40.692507%2C55.614970&z=17&l=map&pt=40.692075%2C55.614979"
    response = requests.get(map_request)
    map_file = "static/img/map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    if current_user.is_authenticated:
        return render_template('about.html', nickname=current_user.nickname,
                               image=current_user.avatar, filename=map_file)
    return render_template('about.html', filename=map_file)


def main():
    db_session.global_init("db/blogs.sqlite")
    app.run(port=32, host='127.0.0.1')


if __name__ == '__main__':
    main()
