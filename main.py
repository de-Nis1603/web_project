from flask import Flask, render_template
from data import db_session
from data.users import User
from data.notices import Notices

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(Notices)
    return render_template("index.html", news=news)


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()