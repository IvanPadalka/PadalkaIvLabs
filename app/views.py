from functools import wraps
from urllib.parse import urlparse, urljoin

from flask import render_template, redirect, flash, url_for, request, abort
from app import app, db
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, PostCreationForm, PostEditingForm, \
    AdminUserUpdateForm, AdminUserCreateForm
from .models import User, Post
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import os
import secrets
from PIL import Image
from datetime import datetime

ROWS_PER_PAGE = 3

@app.route('/')
@app.route('/index')
def show_main_page():
	return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('show_main_page'))
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        email = reg_form.email.data
        password = reg_form.password.data
        
        user = User(username=username, email=email, password_hash=password)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        # Make flash message
        flash(f'Account created for {user.username}', 'info')
        return redirect(url_for('login'))

    return render_template('register.html', form=reg_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('posts'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        remember = login_form.remember.data

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            flash(f'Welcome back {user.username}', 'info')
            login_user(user, remember=remember)
            next_url = request.args.get('next')
            
            if not next_url or url_parse(next_url).netloc != '':
                next_url = url_for('show_main_page')
            return redirect(next_url)

        else:
            flash(f'Incorrect email or password', 'warning')
        
    return render_template('login.html', form=login_form)

@app.route('/posts', methods=['GET'])
@login_required
def posts():
    q = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    if q:
        posts = Post.query.filter(Post.title.contains(q) | Post.body.contains(q))
    else:
        posts = Post.query.order_by(Post.timestamp.desc())

    pages = posts.paginate(page=page, per_page=ROWS_PER_PAGE)
    return render_template('posts.html', posts=posts, pages=pages, q=q)

@app.route('/post/<int:id>')
def post(id):
    post = Post.query.filter_by(id=id).first()
    return render_template('post.html', post=post)


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostCreationForm()
    if form.validate_on_submit():
        post_title = form.post_title.data
        post_body = form.post_body.data

        post = Post(title=post_title, body=post_body, author=current_user)

        db.session.add(post)
        db.session.commit()
        flash("Post created successfully")
    return render_template('create_post.html', form=form)


@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostEditingForm()
    post = Post.query.filter_by(id=id).first()
    if form.validate_on_submit():
        if current_user.username != post.author.username:
            return redirect(url_for('main'))
        post.title = form.post_title.data
        post.body = form.post_body.data
        post.update_time = datetime.utcnow()

        db.session.commit()
        flash("Post edited successfully")

    elif request.method == 'GET':
        if current_user.username != post.author.username:
            return redirect(url_for('main'))
        form.post_title.data = post.title
        form.post_body.data = post.body
    return render_template('edit_post.html', form=form, post=post)


@app.route('/delete_post/<int:id>', methods=["GET", "DELETE"])
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    if current_user.username != post.author.username:
        return redirect(url_for('main'))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('posts'))


@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('show_main_page'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file 
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about_me = form.about_me.data
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about_me.data = current_user.about_me
        form.password.data = current_user.password_hash

    image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
    return render_template('account.html', title='Account', image=image_file, form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    name, ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    output_size = (120, 120)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwags):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwags)
    return decorated_view


@app.route('/admin/')
@login_required
@admin_login_required
def home_admin():
    return render_template('admin_home.html')


@app.route('/admin/users/')
@login_required
@admin_login_required
def users_list_admin():
    users = User.query.all()
    return render_template('admin_users_list.html', users=users)


@app.route('/admin/users/create/', methods=['POST', 'GET'])
@login_required
@admin_login_required
def user_create_admin():
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        admin = form.admin.data
        user = User(username=username, email=email, password_hash=password, admin=admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} has been successfully created!', 'success')
        return redirect(url_for('home_admin'))

    return render_template('admin_create_user.html', form=form)


@app.route('/admin/users/<int:user_id>/update/', methods=['POST', 'GET'])
@login_required
@admin_login_required
def user_update_admin(user_id):
    user = User.query.get(user_id)
    form = AdminUserUpdateForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.admin.data is None:
            user.admin = False
        else:
            user.admin = form.admin.data

        db.session.commit()
        flash(f'User {user.username} has been successfully updated', 'success')
        return redirect(url_for('home_admin'))

    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.admin.data = user.admin
    return render_template('admin_update_user.html', form=form, user=user)


@app.route('/admin/users/<int:user_id>/delete/', methods=['GET'])
@login_required
@admin_login_required
def user_delete_admin(user_id):
    user = User.query.get(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been successfully deleted!', 'success')
    return redirect(url_for('home_admin'))