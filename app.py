import os, functools

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, url_for
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

connect_db(app)


##############################################################################
# User signup/login/logout

##
# LOGIN DECORATOR
# Adapted from https://realpython.com/primer-on-python-decorators/
# 8/22/2018
# and 
#https://blog.teclado.com/handling-the-next-url-when-logging-in-with-flask/
#
# Decorator is added before each route function requiring a user to be logged in.
def login_required(func):
    """Make sure user is logged in before proceeding."""
    @functools.wraps(func)
    def wrapper_login_required(*args, **kwargs):
        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return wrapper_login_required


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect(url_for("homepage"))

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        next_url = request.form.get('next')

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")

            if next_url:
                return redirect(next_url)
            
            else:
                return redirect(url_for("homepage"))

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("Logout successful!", 'success')

    return redirect(url_for("login"))


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
@login_required
def show_following(user_id):
    """Show list of people this user is following."""

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
@login_required
def users_followers(user_id):
    """Show list of followers of this user."""
    
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/<int:user_id>/likes')
@login_required
def users_likes(user_id):
    """Show list of user's liked messages."""

    user = User.query.get_or_404(user_id)
    return render_template('users/likes.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
@login_required
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(url_for("show_following", user_id=g.user.id))


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
@login_required
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(url_for("show_following", user_id=g.user.id))


@app.route('/users/profile', methods=["GET", "POST"])
@login_required
def profile():
    """Update profile for current user."""

    edit_form = EditForm(obj=g.user)
    
    if edit_form.validate_on_submit():

        user = User.authenticate(g.user.username,
                                 edit_form.password.data)

        if user:

            g.user.username = edit_form.username.data
            g.user.email = edit_form.email.data
            g.user.image_url = edit_form.image_url.data
            g.user.header_image_url = edit_form.header_image_url.data
            g.user.bio = edit_form.bio.data
            g.user.location = edit_form.location.data

            db.session.commit()

            flash("Update Successful!", "success")
            return redirect(url_for("users_show", user_id=g.user.id))
        
        else:
            flash("Wrong Password", "danger")
            return render_template('users/edit.html', form=edit_form)

    return render_template('users/edit.html', form=edit_form)


@app.route('/users/delete', methods=["POST"])
@login_required
def delete_user():
    """Delete user."""

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect(url_for("signup"))


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
@login_required
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(url_for("users_show", user_id=g.user.id))


    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/users/add_like/<int:message_id>', methods=["POST"])
@login_required
def messages_like(message_id):
    """Like a message."""

    liked = Likes.query.filter_by(message_id=message_id).first()

    if liked:
        db.session.delete(liked)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == g.user.id).all()

        g.user.likes = likes

        return jsonify(message=f"Message number {message_id} unliked")

    like = Likes(user_id=g.user.id, message_id=message_id)

    db.session.add(like)
    db.session.commit()

    likes = Likes.query.filter(Likes.user_id == g.user.id).all()

    g.user.likes = likes
    return jsonify(message=f"Message number {message_id} liked")


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
@login_required
def messages_destroy(message_id):
    """Delete a message."""

    msg = Message.query.get(message_id)

    if g.user.id != msg.user_id:
        flash("Access unauthorized.", "danger")
        return redirect(url_for("homepage"))

    db.session.delete(msg)
    db.session.commit()

    return redirect(url_for("users_show", user_id=g.user.id))


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:

        # get the ids of all accounts that the user is following
        ids = [user.id for user in g.user.following]
        # include the users own id
        ids.append(g.user.id)

        messages = (Message
                    .query
                    .filter(Message.user_id.in_(ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())


        ids = [msg.id for msg in g.user.likes]

        # liked_msg_ids = [msg.id for msg in likes]

        # messages = (Message.query.order_by(Message.timestamp.desc()).limit(100).all())

        user = User.query.get_or_404(g.user.id)

        return render_template('home.html', messages=messages, likes=ids, user=user)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
