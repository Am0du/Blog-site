from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from model import db, BlogPost
from form import Form, ckeditor
import bleach
from sqlalchemy.exc import IntegrityError
import os
from datetime import date


year = date.today().strftime('%Y')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('s-key')
Bootstrap5(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db.init_app(app)

with app.app_context():
    db.create_all()

ckeditor.init_app(app)

@app.route('/')
def get_all_posts():
    global year
    # TODO: Query the database for all the posts. Convert the data to a python list.
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, year=year)

# TODO: Add a route so that you can click on individual posts.
@app.route('/<int:post_id>')
def show_post(post_id):
    global year
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post, year=year)


# TODO: add_new_post() to create a new blog post
@app.route('/new-post', methods=['POST', 'GET'])
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
                                date=date.today().strftime('%B %d, %Y'), body=body,
                                author=form.author.data, img_url=form.img_url.data)
            db.session.add(new_post)
            db.session.commit()
        except IntegrityError:
            return 'Title already exist in Database'

        return redirect(url_for('get_all_posts'))

    return render_template('make-post.html', path='New Post', form=form,year=year)

# TODO: edit_post() to change an existing blog post
@app.route('/edit_post/<pid>', methods=['POST', 'GET'])
def edit_post(pid):
    global year
    post_id = pid
    user = db.get_or_404(BlogPost, post_id)
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
        user.author = form.author.data
        user.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for('show_post', post_id=user.id))
    return render_template('make-post.html', path='Edit Post', form=form, year=year)
# TODO: delete_post() to remove a blog post from the database
@app.route('/delete')
def delete():
    post_id = request.args.get('post_id')
    user = db.get_or_404(BlogPost, post_id)
    db.session.delete(user)
    db.commit()
    return redirect(url_for('get_all_posts'))

@app.route('/<name>')
def author(name):
    user = db.session.execute(db.select(BlogPost).where(BlogPost.author == name)).scalars()
    return render_template('index.html', all_posts=user)

# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
