from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

login_manager = LoginManager()
db = SQLAlchemy()


# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = 'blogpost'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = relationship('User', back_populates='posts')
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = relationship('Comment', back_populates='parent_post')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship("Comment", back_populates="author")

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey("blogpost.id"))
    parent_post = relationship('BlogPost', back_populates='comments')