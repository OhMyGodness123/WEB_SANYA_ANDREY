from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, \
    SelectField
from wtforms import validators
from vk_user_id import vk_changed_ssilka, old_ssika
from data import db_session, news, users, accounts, comments
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
    email = StringField('Почта', [validators.Email()])
    password = PasswordField('Пароль', [validators.Length(min=5, max=30)])
    password_again = PasswordField('Повторите пароль', [validators.Length(min=5, max=30)])
    name = StringField('Имя пользователя', [validators.Length(min=5, max=30)])
    submit = SubmitField('Зарегистрироваться')


class SaleForm(FlaskForm):
    name = StringField('Название товара:', [validators.Length(min=5, max=80)])
    category = SelectField('Категория:',
                           choices=[('ВК', 'ВК'), ('Telegram', 'Telegram'), ('Steam', 'Steam'),
                                    ('Instagram', 'Instagram'), ('Другое', 'Другое')])
    contact_info = StringField('Ссылка на страницу Вконтакте:', [validators.Length(min=15, max=50)])
    price = StringField('Цена товара:', [validators.Length(min=1, max=30)])
    count = SelectField('Количество товара:',
                        choices=[('1', '1'), ('2', '2'), ('3', '3'),
                                 ('4', '4'), ('5', '5'),
                                 ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')])
    submit = SubmitField('Выставить на продажу')


class LoginForm(FlaskForm):
    email = StringField('Почта', [validators.Email()])
    password = PasswordField('Пароль', [validators.Length(min=5, max=30)])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class ForumForm(FlaskForm):
    message = TextAreaField('Введите своё сообщение:', [validators.Length(min=4, max=4430)])
    submit = SubmitField('Отправить')


class NewsForm(FlaskForm):
    title = StringField('Заголовок:', [validators.Length(min=4, max=166)])
    text = TextAreaField('Содержание:')
    color = StringField('Цвет новости: #')
    category = SelectField('Категория',
                           choices=[('Новости', 'Новости'), ('Софт', 'Софт'), ('Халява', 'Халява'),
                                    ('Обсуждение игр', 'Обсуждение игр')])
    submit = SubmitField('Создать')


class SettingsForm(FlaskForm):
    email = StringField('Почта')
    old_pass = PasswordField('Старый пароль')
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
        texxt = form.text.data.replace('\n', '<br />&nbsp;&nbsp;&nbsp;')
        new.text = texxt
        new.creator = current_user.nickname
        new.color = form.color.data
        new.category = form.category.data
        current_user.news.append(new)
        sessions.merge(current_user)
        sessions.commit()

        new = sessions.query(news.News).filter(news.News.text == texxt).first()

        comment = comments.Comments()
        comment.text = form.text.data.replace('\n', '<br />&nbsp;&nbsp;&nbsp;')
        comment.nickname = current_user.nickname
        comment.for_topic = new.id
        comment.first_com = 'Y'
        sessions.add(comment)
        sessions.commit()

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
        for comment in sessions.query(comments.Comments).filter(
                comments.Comments.for_topic == id).all():
            sessions.delete(comment)
            sessions.commit()
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
        comment = sessions.query(comments.Comments).filter(comments.Comments.for_topic == id,
                                                           comments.Comments.first_com == 'Y').first()
        if new:
            new.title = form.title.data
            new.text = form.text.data
            comment.text = form.text.data
            new.color = form.color.data
            new.category = form.category.data
            sessions.commit()
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
        comment = comments.Comments()
        comment.text = messages.replace('\n', '<br />&nbsp;&nbsp;&nbsp;')
        comment.nickname = current_user.nickname
        comment.for_topic = new.id
        comment.first_com = 'Y'
        session.add(comment)
        session.commit()
    dict_com = []
    for comment in session.query(comments.Comments).filter(
            comments.Comments.for_topic == news_id).all():
        dict_com.append({'text': comment.text, 'author': comment.nickname})
    if current_user.is_authenticated:
        return render_template('discussion.html', nickname=current_user.nickname,
                               image=current_user.avatar, messages=dict_com, form=forum,
                               title=new.title, category=new.category)
    return render_template('discussion.html', messages=dict_com, form=forum, title=new.title,
                           category=new.category)

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


@login_required
@app.route('/profile')
def my_profile():
    return render_template('my_profile.html', title='Todoroki | Мой профиль',
                           nickname=current_user.nickname, image=current_user.avatar,
                           mail=current_user.email, created_date=current_user.date_of_registration)


@login_required
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
                return render_template('settings.html',
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       form=form, message='Пароли не совпадают')
        else:
            return render_template('settings.html',
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   form=form, message='Неверный пароль')
    return render_template('settings.html', title='Todoroki | Настройки',
                           nickname=current_user.nickname, image=current_user.avatar, form=form)


@login_required
@app.route('/add_item', methods=['POST', 'GET'])
def add_item():
    form = SaleForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        acc = accounts.Accounts()
        acc.title = form.name.data
        acc.count = form.count.data
        acc.type = form.category.data
        acc.price = form.price.data
        acc.user_name = current_user.nickname
        try:
            acc.vk_silka = vk_changed_ssilka(form.contact_info.data)
        except TypeError:
            return render_template('add_item.html', form=form, message='Неверная ссылка!')
        session.add(acc)
        session.commit()
        items = session.query(accounts.Accounts).all()
        item_list = {}
        for item in items:
            item_list[item.title] = [item.price, item.count, item.vk_silka, item.user_name,
                                     item.type, item.id, item.user_name]
        if current_user.is_authenticated:
            return render_template('market.html',
                                   nickname=current_user.nickname,
                                   image=current_user.avatar, item_list=item_list)
        return render_template('market.html', item_list=item_list)

    if current_user.is_authenticated:
        return render_template('add_item.html',
                               nickname=current_user.nickname,
                               image=current_user.avatar, form=form)
    return render_template('add_item.html', form=form)


@app.route('/market', methods=['POST', 'GET'])
def market():
    session = db_session.create_session()
    items = session.query(accounts.Accounts).all()
    item_list = {}
    for item in items:
        item_list[item.title] = [item.price, item.count, item.vk_silka, item.user_name,
                                 item.type, item.id, item.user_name]
    if current_user.is_authenticated:
        return render_template('market.html',
                               nickname=current_user.nickname,
                               image=current_user.avatar, item_list=item_list)
    return render_template('market.html', item_list=item_list)


@app.route('/delete_item/<int:id>', methods=['GET', 'POST'])
@login_required
def item_delete(id):
    sessions = db_session.create_session()
    item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
    if item:
        sessions.delete(item)
        sessions.commit()
    else:
        abort(404)
    return redirect('/market')


@app.route('/change_item/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    form = SaleForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if item:
            form.name.data = item.title
            form.category.data = item.type
            form.contact_info.data = old_ssika(item.vk_silka)
            form.price.data = item.price
            form.count.data = item.count
        else:
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if item:
            item.title = form.name.data
            item.type = form.category.data
            item.vk_silka = vk_changed_ssilka(form.contact_info.data)
            item.price = form.price.data
            item.count = form.count.data
            sessions.commit()
            return redirect('/market')
        else:
            abort(404)
    return render_template('add_item.html', form=form,
                           nickname=current_user.nickname, image=current_user.avatar)


@app.route('/market/<category>', methods=['POST', 'GET'])
def sorted_market(category):
    session = db_session.create_session()
    if category == 'vk':
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'ВК')
    elif category == 'telegram':
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Telegram')
    elif category == 'steam':
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Steam')
    elif category == 'instagram':
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Instagram')
    item_list = {}
    for item in items:
        item_list[item.title] = [item.price, item.count, item.vk_silka, item.user_name,
                                 item.type, item.id, item.user_name]
    if current_user.is_authenticated:
        return render_template('market.html',
                               nickname=current_user.nickname,
                               image=current_user.avatar, item_list=item_list)
    return render_template('market.html', item_list=item_list)


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
    app.run(port=1414, host='127.0.0.1')


if __name__ == '__main__':
    main()
