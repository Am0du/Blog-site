from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap5
from model import db, BlogPost, login_manager, login_user, logout_user, current_user, User, Comment
from form import Form, ckeditor, RegisterForm, LoginForm, CommentForm
import bleach
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import os
from datetime import date
from flask_gravatar import Gravatar


year = date.today().strftime('%Y')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('s-key')
Bootstrap5(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_url')
db.init_app(app)

#login manager
login_manager.init_app(app)

# def is_user_admin():
#     if current_user.id == author.id:
#         return True
# def admin_only(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         post_id = kwargs.get('post_id')
#         user = db.get_or_404(BlogPost, post_id)
#         if current_user.id == user.author_id:
#             return func(*args, **kwargs)
#         else:
#             abort(403)
#             return 'This is a restricted page.'
#     return wrapper

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return func(*args, **kwargs)
    return decorated_view


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

with app.app_context():
    db.create_all()

ckeditor.init_app(app)

@app.route('/')
def get_all_posts():
    global year
    # TODO: Query the database for all the posts. Convert the data to a python list.
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, year=year, logged_in=current_user.is_authenticated)

# TODO: Add a route so that you can click on individual posts.
@app.route('/<int:post_id>', methods=['POST', 'GET'])
def show_post(post_id):
    global year
    form = CommentForm()
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = db.get_or_404(BlogPost, post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to login or register')
            return redirect(url_for('login'))
        else:
            new_comment = Comment(text=form.body.data, author=current_user, parent_post=requested_post,)
            db.session.add(new_comment)
            db.session.commit()
    return render_template("post.html", post=requested_post, year=year, form=form, logged_in=current_user.is_authenticated)

# TODO: add_new_post() to create a new blog post
@app.route('/new-post', methods=['POST', 'GET'])
@login_required
def new_post():
    global year
    form = Form()
    if form.validate_on_submit():
        try:
            body = bleach.clean(form.body.data, tags=['p', 'img', 'h2', 'h1', 'a', 'abbr', 'acronym', 'b',
                                                      'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul'],
                                attributes={'img': ['alt', 'src', 'style'], 'a': ['href', 'title'],
                                            'abbr': ['title'], 'acronym': ['title']})

            new_post = BlogPost(title=form.title.data, subtitle=form.subtitle.data,
                                date=date.today().strftime('%B %d, %Y'), body=body,author=current_user, img_url=form.img_url.data)
            db.session.add(new_post)
            db.session.commit()
        except IntegrityError:
            return 'Title already exist in Database'

        return redirect(url_for('get_all_posts'))

    return render_template('make-post.html', path='New Post', form=form,year=year, logged_in=current_user.is_authenticated)

# TODO: edit_post() to change an existing blog post
@app.route('/edit_post/<pid>', methods=['POST', 'GET'])
def edit_post(pid):
    global year

    post_id = pid
    user = db.get_or_404(BlogPost, post_id)
    try:
        if current_user.id == user.author_id:
            form = Form(
            title=user.title,
            subtitle=user.subtitle,
            img_url=user.img_url,
            author=user.author,
            body=user.body
            )
            if form.validate_on_submit():
                user.title = form.title.data
                user.body = form.body.data
                user.subtitle = form.subtitle.data
                user.author = current_user
                user.img_url = form.img_url.data
                db.session.commit()
                return redirect(url_for('show_post', post_id=user.id))
            return render_template('make-post.html', path='Edit Post', form=form, year=year, logged_in=current_user.is_authenticated)
    except AttributeError:
        return redirect(url_for('get_all_posts'))
# TODO: delete_post() to remove a blog post from the database

@app.route('/delete')
# @admin_only
def delete():
    post_id = request.args.get('post_id')
    user = db.get_or_404(BlogPost, post_id)
    db.session.delete(user)
    db.commit()
    return redirect(url_for('get_all_posts'))

@app.route('/<name>')
def author(name):
    author = db.session.query(User).filter_by(name=name).first()
    return redirect(url_for('get_all_posts', all_posts=author, logged_in=current_user.is_authenticated))

@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)

@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        new_pass = generate_password_hash(password=request.form.get('password'), salt_length=18)
        try:
            new_user = User(name=request.form.get('name'), password=new_pass, email=request.form.get('email'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('login'))
        except IntegrityError:
            flash('Email already exists')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        user = db.session.execute(db.select(User).where(User.email == request.form.get('email'))).scalar()
        print(user)
        if user is None:
            flash('Invalid credentials')
            return redirect(url_for('login'))
        elif check_password_hash(pwhash=user.password, password=request.form.get('password')):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    app.run(debug=True, port=5003)
