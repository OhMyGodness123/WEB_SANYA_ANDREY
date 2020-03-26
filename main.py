from flask import Flask, render_template, redirect

app = Flask(__name__)


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
    app.run(port=5111, host='127.0.0.1')


if __name__ == '__main__':
    main()
