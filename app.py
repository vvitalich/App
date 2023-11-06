from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean(), default=False)


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255))
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    expiry_timestamp = db.Column(db.DateTime)
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    users = User.query.all()
    tokens = Token.query.all()
    return render_template('index.html',
                           users=users, tokens=tokens)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        current_datetime = datetime.utcnow()
        new_datetime = current_datetime + timedelta(hours=24)
        name = request.form['name']
        email = request.form['email']

        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()

        token = Token(token=secrets.token_urlsafe(16),
                      user_id=user.id, expiry_timestamp=new_datetime)
        db.session.add(token)
        db.session.commit()

        return redirect('/')

    return render_template('add_user.html')


@app.route('/user_info/<int:id>', methods=['GET', 'POST'])
def verify_token(id):
    user = User.query.filter_by(id=id).first()
    token = Token.query.filter_by(user_id=id).first()

    left_to_live = ['Invalid', None]
    if datetime.now() < token.expiry_timestamp:
        left_to_live[0] = 'Valid'
        left_to_live[1] = token.expiry_timestamp - datetime.now()

    return render_template('user_info.html',
                           user=user, token=token, left_to_live=left_to_live)


@app.route('/user_info_token/<string:token>', methods=['POST'])
def email_verifi(token):
    if request.method == 'POST':
        token = Token.query.filter_by(token=token).first()
        user = User.query.get(token.user_id)

        if user.email_verified == False:
            if token.expiry_timestamp > datetime.utcnow():
                user.email_verified = True
                token.expiry_timestamp = datetime.utcnow()
                db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run()
