from flask import Flask, render_template, redirect, abort, request
from data import db_session
from data.users import User
from data.notices import Notices
from forms.user import RegisterForm, LoginForm
from forms.notices import NoticeForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


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
        current_user.notices.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('notices.html', title='Добавление объявления',
                           form=form)


@app.route('/notice/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    print(7)
    form = NoticeForm()
    if request.method == "GET":
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
        db_sess = db_session.create_session()
        news = db_sess.query(Notices).filter(Notices.id == id,
                                          Notices.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.points = form.points.data
            db_sess.commit()
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
    news = db_sess.query(Notices).filter(Notices.id == id,
                                      Notices.user == current_user
                                      ).first()
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