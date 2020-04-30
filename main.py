from flask import Flask, render_template, redirect, request, make_response, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, \
    SelectField
from wtforms import validators
from vk_user_id import vk_changed_ssilka, old_ssika
from data import db_session, news, users, accounts, comments
import random
import requests
from flask_restful import abort, Api
import bbcodepy
import Api_news
from flask_ngrok import run_with_ngrok

# подключение библиотек и функций


app = Flask(__name__)  # создание приложения
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'  # создание ключа
login_manager = LoginManager()
login_manager.init_app(app)
UPLOAD_FOLDER = 'static/img/'  # путь для сохранения картинок
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # путь для сохранения картинок
api = Api(app)


@login_manager.user_loader
def load_user(user_id):  # функция для загрузки пользователя
    sessions = db_session.create_session()
    return sessions.query(users.User).get(user_id)


@app.errorhandler(404)  # функция ошибки
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


class RegisterForm(FlaskForm):  # класс формы регистрации
    email = StringField('Почта', [validators.Email()])
    password = PasswordField('Пароль')
    password_again = PasswordField('Повторите пароль')
    name = StringField('Имя пользователя')
    submit = SubmitField('Зарегистрироваться')


class SaleForm(FlaskForm):  # класс формы продажи аккаунтов
    name = StringField('Название товара:')
    category = SelectField('Категория:',
                           choices=[('ВК', 'ВК'), ('Telegram', 'Telegram'), ('Steam', 'Steam'),
                                    ('Instagram', 'Instagram'), ('Другое', 'Другое')])
    contact_info = StringField('Ссылка на страницу Вконтакте:')
    price = StringField('Цена товара:')
    count = SelectField('Количество товара:',
                        choices=[('1', '1'), ('2', '2'), ('3', '3'),
                                 ('4', '4'), ('5', '5'),
                                 ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')])
    submit = SubmitField('Выставить на продажу')


class LoginForm(FlaskForm):  # класс формы авторизации
    email = StringField('Почта')
    password = PasswordField('Пароль')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class ForumForm(FlaskForm):  # класс формы обсуждения
    message = TextAreaField('Введите своё сообщение:')
    submit = SubmitField('Отправить')


class NewsForm(FlaskForm):  # класс формы создания новости
    title = StringField('Заголовок:')
    text = TextAreaField('Содержание:')
    color = StringField('Цвет новости: #')
    category = SelectField('Категория',
                           choices=[('Новости', 'Новости'), ('Софт', 'Софт'), ('Халява', 'Халява'),
                                    ('Обсуждение игр', 'Обсуждение игр')])
    submit = SubmitField('Создать')


class SettingsForm(FlaskForm):  # класс формы настроек
    email = StringField('Почта', [validators.Email()])
    old_pass = PasswordField('Старый пароль')
    new_pass = PasswordField('Новый пароль')
    new_pass_again = PasswordField('Подтвердите новый пароль')
    submit = SubmitField('Сохранить')


@app.route('/logout')  # выход пользователя из системы
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/news', methods=['GET', 'POST'])  # добавление новости
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():

        sessions = db_session.create_session()
        new = news.News()
        if len(form.title.data) <= 5:  # проверка длины заголовка
            return render_template('add_news.html', form=form,
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   title='Редактирование', message='Пожалуйста,'
                                                                   ' сформулируйте заголовок'
                                                                   ' темы более подробно')
        if len(form.text.data) <= 15:  # проверка длины текста темы
            return render_template('add_news.html', form=form,
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   title='Редактирование', message='Пожалуйста,'
                                                                   ' сформулируйте ваш'
                                                                   ' текст более подробно'
                                                                   ' (Более 15 знаков)')
        new.title = form.title.data
        text2 = form.text.data

        new.text = text2
        new.creator = current_user.nickname
        new.color = form.color.data
        new.category = form.category.data
        current_user.news.append(new)
        sessions.merge(current_user)
        sessions.commit()

        # добавляем текст в сущность новостей

        new = sessions.query(news.News).filter(news.News.text == text2).first()

        comment = comments.Comments()
        comment.text = form.text.data
        comment.nickname = current_user.nickname
        comment.for_topic = new.id
        comment.first_com = 'Y'
        sessions.add(comment)
        sessions.commit()

        # добавляем текст в сущность коментариев

        return redirect('/')  # возвращаем пользователя на главную страницу
    return render_template('add_news.html', title='Добавление новости', form=form,
                           nickname=current_user.nickname, image=current_user.avatar)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])  # удаление новости через её id
@login_required
def news_delete(id):
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.id == id).first()
    if new:  # если такая новость существует то удаляем
        sessions.delete(new)
        sessions.commit()
        for comment in sessions.query(comments.Comments).filter(
                comments.Comments.for_topic == id).all():
            sessions.delete(comment)
            sessions.commit()
    else:  # иначе выбрасываем ошибку 404
        abort(404)
    return redirect('/')  # возвращаем пользователя на главную страницу


@app.route('/change_news/<int:id>', methods=['GET', 'POST'])  # изменение новости
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id).first()
        if new:  # проверка на существование новости
            form.title.data = new.title
            form.text.data = new.text
            form.category.data = new.category
            form.color.data = new.color
        else:  # если такой нововсти нет
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id).first()
        comment = sessions.query(comments.Comments).filter(comments.Comments.for_topic == id,
                                                           comments.Comments.first_com ==
                                                           'Y').first()
        # нахождение первого комментария для его изменения

        if new:  # если новость сформулированна
            if len(form.title.data) <= 5:  # проверка длины заголовка
                return render_template('add_news.html', form=form,
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       title='Редактирование', message='Пожалуйста,'
                                                                       ' сформулируйте заголовок'
                                                                       ' темы более подробно')
            if len(form.text.data) <= 15:  # проверка длины текста темы
                return render_template('add_news.html', form=form,
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       title='Редактирование', message='Пожалуйста,'
                                                                       ' сформулируйте ваш'
                                                                       ' текст более подробно'
                                                                       ' (Более 15 знаков)')
            new.title = form.title.data
            new.text = form.text.data
            comment.text = form.text.data
            new.color = form.color.data
            new.category = form.category.data
            sessions.commit()
            # сохранение новости и комментария к нему
            return redirect('/')
        else:
            abort(404)
    return render_template('add_news.html', form=form,
                           nickname=current_user.nickname, image=current_user.avatar,
                           title='Редактирование')


@app.route('/login', methods=['GET', 'POST'])  # вход на сайт
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):  # проверка на пароль
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        elif user:  # проверка существует ли вообще этот пользователь
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        else:
            return render_template('login.html',
                                   message="Такого пользователя не существует",
                                   form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])  # регистрация пользователя
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        try:  # если пользователь указал свою аватарку
            file = request.files['file']
            path = app.config['UPLOAD_FOLDER'] + file.filename
            file.save(path)
        except Exception:  # если не указал то рандомно выбирается
            img = random.choice(['avatar1.png', 'avatar2.png', 'avatar3.png', 'avatar4.png',
                                 'avatar5.png', 'avatar6.png', 'avatar7.png'])
            path = f"static/img/{img}"
        if form.password.data != form.password_again.data:  # если введеные пароли не совпадают
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(users.User).filter(
                users.User.nickname == form.name.data).first():  # если такой никнейм занят
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if session.query(users.User).filter(
                users.User.email == form.email.data).first():  # если такая почта занята
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="На данную почту уже зарегистирован аккаунт")
        if len(form.password.data) <= 5:  # проверка на длину пароля
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Вы ввели слишком простой пароль. \n\n\n"
                                           "Длина хорошего пароля больше 5 символов")
        if len(form.name.data) <= 3:  # проверка на длину логина
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Вы ввели слишком короткое имя пользователя")
        user = users.User(
            nickname=form.name.data,
            email=form.email.data,
            avatar='/' + path
        )  # создание пользователя
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/")  # главная страница
def index():
    session = db_session.create_session()
    new = session.query(news.News).all()
    new.reverse()  # переворачиваем все новости, чтобы новые новости были сверху
    if current_user.is_authenticated:  # если пользователь авторизован
        return render_template('forum.html', title='Todoroki', nickname=current_user.nickname,
                               image=current_user.avatar, news=new)
    return render_template('forum.html', title='Todoroki', news=new)


@app.route("/discussion/<int:news_id>",
           methods=['GET', 'POST'])  # страница обсуждения темы по её id
def discussion(news_id):
    forum = ForumForm()  # форма для оставления комментариев
    session = db_session.create_session()
    dict_com = []  # список словарей нужен для передачи комментариев в html
    for comment in session.query(comments.Comments).filter(
            comments.Comments.for_topic == news_id).all():
        dict_com.append(
            {'text': bbcodepy.Parser().to_html(comment.text), 'author': comment.nickname})
    new = session.query(news.News).filter(news.News.id == news_id).first()
    messages = forum.message.data
    if forum.validate_on_submit():
        comment = comments.Comments()
        if len(messages) <= 4:  # проверяем длину комментария
            return render_template('discussion.html', nickname=current_user.nickname,
                                   image=current_user.avatar, messages=dict_com, form=forum,
                                   title=new.title, category=new.category,
                                   message='Сформулируйте, свой комментарий более подробно')
        comment.text = messages
        comment.nickname = current_user.nickname
        comment.for_topic = new.id
        comment.first_com = 'N'
        session.add(comment)
        session.commit()
        dict_com.append(
            {'text': bbcodepy.Parser().to_html(comment.text), 'author': comment.nickname})
        # добавляем новый комментарий

    if current_user.is_authenticated:
        return render_template('discussion.html', nickname=current_user.nickname,
                               image=current_user.avatar, messages=dict_com, form=forum,
                               title=new.title, category=new.category)
    return render_template('discussion.html', messages=dict_com, form=forum, title=new.title,
                           category=new.category)


@app.route("/<category>")  # сортировка тем по категориям
def sorted_news(category):
    session = db_session.create_session()
    if category == 'only_games':  # только темы посвященные Обсуждению игр
        new = session.query(news.News).filter(news.News.category == 'Обсуждение игр').all()
    elif category == 'only_soft':  # только темы посвященные Софту
        new = session.query(news.News).filter(news.News.category == 'Софт').all()
    elif category == 'only_halyava':  # только темы посвященные Халяве
        new = session.query(news.News).filter(news.News.category == 'Халява').all()
    else:  # все темы
        new = session.query(news.News).filter(news.News.category == 'Новости').all()
    new.reverse()
    if current_user.is_authenticated:
        return render_template('forum.html', title='Todoroki', nickname=current_user.nickname,
                               image=current_user.avatar, news=new)
    return render_template('forum.html', title='Todoroki', news=new)


@login_required
@app.route('/profile')  # профиль пользователя
def my_profile():
    return render_template('my_profile.html', title='Todoroki | Мой профиль',
                           nickname=current_user.nickname, image=current_user.avatar,
                           mail=current_user.email, created_date=current_user.date_of_registration)


@login_required
@app.route('/settings',
           methods=['GET', 'POST'])  # настройки пользователя для смены почты или пароля
def settings():
    form = SettingsForm()
    form.email.data = current_user.email
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.id == current_user.id).first()
        if user.check_password(form.old_pass.data):  # проверка чтобы старый пароль совпадал
            if form.new_pass.data == form.new_pass_again.data and form.new_pass_again.data != '':
                # проверка чтобы новые пароли совпадали
                if len(form.new_pass_again.data) >= 5:
                    if user:
                        user.set_password(form.new_pass.data)  # меняем пароль
                        session.commit()
                        return redirect('/')
                    else:
                        abort(404)
                else:
                    return render_template('settings.html',
                                           nickname=current_user.nickname,
                                           image=current_user.avatar,
                                           form=form, message='Вы ввели слишком простой пароль. '
                                                              'Длина хорошего пароля '
                                                              'больше 5 символов')
            elif current_user.email != form.email.data:  # если старая почта была изменена
                user.email = form.email.data
                session.commit()
                return redirect('/')
            elif form.new_pass_again.data != '' or form.new_pass.data != '':
                # если новые пароли не совпали
                return render_template('settings.html',
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       form=form, message='Новые пароли не совпадают')
        else:  # если старый пароль не совпадает
            return render_template('settings.html',
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   form=form, message='Для подтверждения действий нужно ввести'
                                                      ' старый пароль. У вас введён'
                                                      ' неверный пароль.')
    return render_template('settings.html', title='Todoroki | Настройки',
                           nickname=current_user.nickname, image=current_user.avatar, form=form)


@login_required
@app.route('/add_item', methods=['POST', 'GET'])  # размещение аккаунта
def add_item():
    form = SaleForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        item = accounts.Accounts()
        if len(form.name.data) <= 5:    # проверка короткого названия
            return render_template('add_item.html', form=form,
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   message='Название товара должно быть больше 5 символов')
        item.title = form.name.data
        item.type = form.category.data
        new_ssilka = vk_changed_ssilka(form.contact_info.data)
        if len(form.contact_info.data) < 15 or new_ssilka == 'error':  # проверка ссылки вк
            return render_template('add_item.html', form=form,
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   message='Введите корректную ссылку ВК. Без сокращений')
        item.vk_silka = new_ssilka
        item.price = form.price.data
        if len(form.price.data) > 8:  # проверка чтобы цена не была слишком большой
            return render_template('add_item.html', form=form,
                                   nickname=current_user.nickname, image=current_user.avatar,
                                   message='Слишком большая цена для аккаунта.')
        item.count = form.count.data
        item.user_name = current_user.nickname
        session.add(item)
        session.commit()
        items = session.query(accounts.Accounts).all()
        item_list = {}  # словарь для товаров
        for item in items:  # получение всех товаров, чтобы разместить на странице
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


@app.route('/market', methods=['POST', 'GET'])  # страница маркета
def market():
    session = db_session.create_session()
    items = session.query(accounts.Accounts).all()
    item_list = {}  # словарь для товаров
    for item in items:  # получение всех товаров, чтобы разместить на странице
        item_list[item.title] = [item.price, item.count, item.vk_silka, item.user_name,
                                 item.type, item.id, item.user_name]
    if current_user.is_authenticated:
        return render_template('market.html',
                               nickname=current_user.nickname,
                               image=current_user.avatar, item_list=item_list)
    return render_template('market.html', item_list=item_list)


@app.route('/delete_item/<int:id>', methods=['GET', 'POST'])  # удаление аккаунта по id
@login_required
def item_delete(id):
    sessions = db_session.create_session()
    item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
    if item:  # проверка на существование аккаунта
        sessions.delete(item)
        sessions.commit()
    else:  # если такого аккаунта нет, то выбрасываем ошибку 404
        abort(404)
    return redirect('/market')


@app.route('/change_item/<int:id>', methods=['GET', 'POST'])  # изменение аккаунта по его id
@login_required
def edit_item(id):
    form = SaleForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if item:  # проверка на существование аккаунта
            form.name.data = item.title
            form.category.data = item.type
            form.contact_info.data = old_ssika(item.vk_silka)
            form.price.data = item.price
            form.count.data = item.count
        else:  # если такого аккаунта нет, то выбрасываем ошибку 404
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        item = sessions.query(accounts.Accounts).filter(accounts.Accounts.id == id).first()
        if item:
            if len(form.name.data) <= 5:
                return render_template('add_item.html', form=form,
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       message='Название товара должно быть больше 5 символов')
            item.title = form.name.data
            item.type = form.category.data
            item.vk_silka = vk_changed_ssilka(form.contact_info.data)
            if len(form.contact_info.data) < 15:
                return render_template('add_item.html', form=form,
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       message='Введите корректную ссылку ВК. Без сокращений')
            item.price = form.price.data
            if len(form.price.data) > 8:
                return render_template('add_item.html', form=form,
                                       nickname=current_user.nickname, image=current_user.avatar,
                                       message='Слишком большая цена для аккаунта.')
            item.count = form.count.data
            sessions.commit()
            return redirect('/market')
        else:
            abort(404)
    return render_template('add_item.html', form=form,
                           nickname=current_user.nickname, image=current_user.avatar)


@app.route('/market/<category>', methods=['POST', 'GET'])  # сортировка аккаунтов
def sorted_market(category):
    session = db_session.create_session()
    if category == 'vk':  # только аккаунты ВК
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'ВК')
    elif category == 'telegram':  # только аккаунты Telegram
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Telegram')
    elif category == 'steam':  # только аккаунты Steam
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Steam')
    elif category == 'instagram':  # только аккаунты Instagram
        items = session.query(accounts.Accounts).filter(accounts.Accounts.type == 'Instagram')
    else:  # все аккаунты
        items = session.query(accounts.Accounts).all()
    item_list = {}  # словарь для товаров
    for item in items:  # получение всех товаров, чтобы разместить на странице
        item_list[item.title] = [item.price, item.count, item.vk_silka, item.user_name,
                                 item.type, item.id, item.user_name]
    if current_user.is_authenticated:
        return render_template('market.html',
                               nickname=current_user.nickname,
                               image=current_user.avatar, item_list=item_list)
    return render_template('market.html', item_list=item_list)


@app.route('/about')  # страница контактов
def about():
    map_request = "https://static-maps.yandex.ru/1.x/?ll=40.692507%2C55.614970&z=17&l" \
                  "=map&pt=40.692075%2C55.614979"  # гео запрос
    response = requests.get(map_request)
    map_file = "static/img/map.png"  # путь куда сохранять карту
    with open(map_file, "wb") as file:
        file.write(response.content)  # получение карты наших координат
    if current_user.is_authenticated:
        return render_template('about.html', nickname=current_user.nickname,
                               image=current_user.avatar, filename=map_file)
    return render_template('about.html', filename=map_file)


db_session.global_init("db/blogs.sqlite")  # иницилизация БД
api.add_resource(Api_news.NewsListResource, '/api/v1/news')  # иницилизация API
api.add_resource(Api_news.NewsResource, '/api/v1/news/<int:news_id>')
app.run(port=1421, host='127.0.0.1')  # запуск приложения