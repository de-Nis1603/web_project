from flask import Flask, render_template, redirect, abort, request, url_for
from data import db_session
from data.users import User
from data.notices import Notices
from forms.user import RegisterForm, LoginForm
from forms.notices import NoticeForm
from forms.add_point import AddPointForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import io
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import requests

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def bytes_to_image_matplotlib(byte_data):
    image = mpimg.imread(io.BytesIO(byte_data), format='PNG')
    return image


def coordinates_finder(name):
    import requests
    insert_data = 'Москва ' + name
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode={insert_data}&format=json"

    # Выполняем запрос.
    response = requests.get(geocoder_request)
    if response:
        # Преобразуем ответ в json-объект
        json_response = response.json()

        # Получаем первый топоним из ответа геокодера.
        # Согласно описанию ответа, он находится по следующему пути:
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        # Полный адрес топонима:
        toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
        # Координаты центра топонима:
        toponym_coodrinates = toponym["Point"]["pos"]
        # Печатаем извлечённые из ответа поля:
        return toponym_coodrinates
    else:
        return 'invalid request'

def map_creator(points, id):
    print('creating a map')
    map_request = "http://static-maps.yandex.ru/v1?lang=ru_RU&pt="
    invalids = []
    put_on_the_map = []
    verticals = []
    horizontals = []
    for point in points.split('\n'):
        print(point)
        point_cs = coordinates_finder(point).split()
        if point_cs == 'invalid request':
            invalids.append(point)
        else:
            put_on_the_map.append(str(point_cs[0]) + "," + str(point_cs[1]) + ',pm2rdm')
            verticals.append(float(point_cs[0]))
            horizontals.append(float(point_cs[1]))
    print(put_on_the_map)
    print('verticals')
    print(verticals)
    if put_on_the_map:
        if len(put_on_the_map) == 1:
            map_request = f"http://static-maps.yandex.ru/1.x/?ll={verticals[0]},{horizontals[0]}&z=13&l=map&pt={verticals[0]},{horizontals[0]},pm2rdm"
        else:
            medium_verticals = (max(verticals) + min(verticals)) / 2
            medium_horizontal = (max(horizontals) + min(horizontals)) / 2
            map_request = f"http://static-maps.yandex.ru/1.x/?ll={medium_verticals},{medium_horizontal}&l=map&pt="
            map_request += "~".join(put_on_the_map)
    else:
        map_request = "http://static-maps.yandex.ru/1.x/?ll=37.612969,55.742748&z=10&l=map"
    print(map_request)
    response = requests.get(map_request)
    print(response)
    if response:
        print(100)
    map_file = f"static/maps/map{id}.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    return invalids


@login_manager.user_loader
def load_user(user_id):
    print(1)
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    print(2)
    db_sess = db_session.create_session()
    news = db_sess.query(Notices)
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(3)
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    print(4)
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    print(5)
    logout_user()
    return redirect("/")


@app.route('/notice',  methods=['GET', 'POST'])
@login_required
def add_news():
    print(6)
    form = NoticeForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = Notices()
        news.title = form.title.data
        news.content = form.content.data
        news.points = form.points.data
        photo_bytes_array = form.image.data
        print(photo_bytes_array)
        current_user.notices.append(news)
        db_sess.merge(current_user)
        last_id = len(db_sess.query(Notices).all())
        db_sess.commit()
        photo_bytes_array = form.image.data
        form.image.data.save(f'static/photos/{last_id}.png')
        map_creator(news.points, last_id)
        return redirect('/')
    return render_template('notices.html', title='Добавление объявления',
                           form=form)


@app.route("/add_point/<int:id>", methods=['GET', 'POST'])
@login_required
def add_point(id):
    form = AddPointForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(Notices).filter(Notices.id == id).first()
        if news:
            news.points += "\n" + form.points.data
            print(news.points)
            db_sess.commit()
            map_creator(news.points, id)
            # сюда прописать обработчик для создания фотографии карты
            return redirect('/')
        else:
            abort(404)
    return render_template('add_point.html', title='Добавление метки',
                           form=form)


@app.route('/pain_rating')
@login_required
def rating_boli():
    return render_template('rating.html', ref=url_for('static', filename='rating.png'), ref2=url_for('static', filename='rating_map.png'))


@app.route('/notice/watch/<int:id>')
def watch_notice(id):
    db_sess = db_session.create_session()
    needed_notice = db_sess.query(Notices).filter(Notices.id == id).first()
    return render_template('watch.html', name=needed_notice.title, description=needed_notice.content,
                           owner=needed_notice.user.name, id=id, ref=url_for('static', filename=f'maps/map{id}.png'),
                           ref_photo=url_for('static', filename=f'photos/{id}.png'))


@app.route('/notice/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    print('came to edit ' + str(id))
    form = NoticeForm()
    if request.method == "GET":
        print('get method')
        db_sess = db_session.create_session()
        news = db_sess.query(Notices).filter(Notices.id == id,
                                          Notices.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.points.data = news.points
        else:
            abort(404)
    if form.validate_on_submit():
        print('validate')
        db_sess = db_session.create_session()
        news = db_sess.query(Notices).filter(Notices.id == id,
                                             Notices.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.points = form.points.data
            db_sess.commit()
            print('db committed')
            map_creator(form.points.data, id)
            print(0)
            photo_bytes_array = form.image.data
            form.image.data.save(f'static/photos/{id}.png')
            map_creator(news.points, id)
            print(6)
            # сюда прописать обработчик для создания фотографии карты
            return redirect('/')
        else:
            abort(404)
    return render_template('notices.html',
                           title='Редактирование объявления',
                           form=form
                           )


@app.route('/notice_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    if current_user.id == 1:
        news = db_sess.query(Notices).filter(Notices.id == id).first()
    else:
        news = db_sess.query(Notices).filter(Notices.id == id,
                                             Notices.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')

def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()