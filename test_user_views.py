"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from flask import url_for

from models import db, connect_db, Message, User, Likes
from sqlalchemy.exc import IntegrityError, InvalidRequestError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        self.mrsturtle = User.signup(username= "MrsTurtle",
                                    password= "TEST_PASSWORD",
                                    email= "mrsturtle@test.com",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up after tests."""

        db.session.rollback()
    
    def test_signup_and_logout(self):

        with app.test_client() as c:

            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Join Warbler today.</h2>""", html)

            data = {
                "username": "MrTurtle",
                "password": "TEST_PASSWORD",
                "email": "turtle@test.com"
                }

            resp = c.post('/signup', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@MrTurtle</p>", html)

            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


            duplicate_data = {
                "username": "MrTurtle",
                "password": "TEST_PASSWORD",
                "email": "different_email@test.com"
                }
            
            # attempt to signup with a duplicate username
            resp = c.post('/signup', data=duplicate_data)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Join Warbler today.</h2>""", html)
            
    def test_log_in(self):
        """Test user log in."""

        with app.test_client() as c:

            resp = c.get('/login')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


            data = {"username" : "testuser",
                    "password" : "testuser"}

            resp = c.post('/login', data=data, follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)

            wrong_password = {"username" : "testuser",
                    "password" : "fake_password"}

            # attempt login with wrong password
            resp = c.post('/login', data=wrong_password, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

            wrong_username = {"username" : "fake_username",
            "password" : "testuser"}

            # attempt login with wrong username
            resp = c.post('/login', data=wrong_username, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


    def test_users(self):
        """Test users list."""

        with app.test_client() as c:

            data = {
                "username": "MrTurtle",
                "password": "TEST_PASSWORD",
                "email": "turtle@test.com"
                }

            c.post('/signup', data=data)

            resp = c.get('/users')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)
            self.assertIn("<p>@MrTurtle</p>", html)
            self.assertIn("<p>@MrsTurtle</p>", html)


            resp = c.get(url_for('list_users', q="MrTurtle"))
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("<p>@testuser</p>", html)
            self.assertIn("<p>@MrTurtle</p>", html)
            self.assertNotIn("<p>@MrsTurtle</p>", html)


    def test_users_id(self):
        """Test user detail page."""

        with app.test_client() as c:
            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h4 id="sidebar-username">@testuser</h4>""", html)

    def test_user_follow_and_stop_following(self):
        """Test that a user can follow another user."""
        with app.test_client() as c:

            # attempt to follow while logged out
            resp = c.post(f'/users/follow/{self.testuser.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

            data = {
                "username": "MrTurtle",
                "password": "TEST_PASSWORD",
                "email": "turtle@test.com"
                }

            # sign up a user, test follow, then unfollow
            c.post('/signup', data=data)
            
            resp = c.post(f'/users/follow/{self.testuser.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)

            resp = c.post(f'/users/stop-following/{self.testuser.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("<p>@testuser</p>", html)

    

    def test_user_following_and_followers(self):
        """Test user following."""
        with app.test_client() as c:

            data = {
                "username": "MrsTurtle",
                "password": "TEST_PASSWORD",
                }

            # login a user, test follow, then test that they appear in '/users/following'
            c.post('/login', data=data)

            resp = c.post(f'/users/follow/{self.testuser.id}', follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)

            resp = c.get(f'/users/{self.mrsturtle.id}/following', follow_redirects=True)

            # check that the user card appears
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)

            # log user out, log followed user in, test that original user appears in '/users/followers'

            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


            data = {
                "username": "testuser",
                "password": "testuser",
                }

            resp = c.post('/login', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser</p>", html)


            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@MrsTurtle</p>", html)

            # logout user, and check that a user's following page can't be viewed
            c.get('/logout')

            resp = c.get(f'/users/{self.mrsturtle.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)






    def test_user_likes(self):
        """Test user liked messages."""

        with app.test_client() as c:
                
            # make a test message
            msg = Message(
                text="This is a test message by testuser.",
                timestamp="2016-12-06 23:13:29.694274",
                user_id=self.testuser.id
            )

            db.session.add(msg)
            db.session.commit()

            data = {
                "username": "MrsTurtle",
                "password": "TEST_PASSWORD",
                }

            # login a user and add a like to the test message
            c.post('/login', data=data)

            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            data = resp.json

            self.assertEqual(resp.status_code, 200)
            self.assertEqual({"message" : f"Message number {msg.id} liked"}, data)
            
            # test that message appears in '/users/likes'
            resp = c.get(f'/users/{self.mrsturtle.id}/likes')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<p>This is a test message by testuser.</p>""", html)

            # unlike the message, and test that it doesn't appear in 'users/likes'
            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            data = resp.json

            self.assertEqual(resp.status_code, 200)
            self.assertEqual({"message" : f"Message number {msg.id} unliked"}, data)

            resp = c.get(f'/users/{self.mrsturtle.id}/likes')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("""<p>This is a test message by testuser.</p>""", html)

            # logout user then try the like routes
            c.get('/logout')

            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

            resp = c.get(f'/users/{self.mrsturtle.id}/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


    def test_user_edit_profile(self):
        """Test user edit profile."""

        with app.test_client() as c:
        
            data = {
                    "username": "MrsTurtle",
                    "password": "TEST_PASSWORD",
                    }

            # login a user, then get the edit form
            c.post('/login', data=data)

            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Edit Your Profile.</h2>""", html)
                  
            data = {
                "username": "MrsTurtle",
                "email": "mrsturtle@test.com",
                "image_url" : "/static/images/default-pic.png",
                "header_image_url" : "/static/images/warbler-hero.jpg",
                "bio" : "I am Mrs Turtle",
                "location" : "Florida",
                "password" : "TEST_PASSWORD"
                }

            # make an edit, and test that it works
            resp = c.post('/users/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>I am Mrs Turtle</p>", html)

            data = {
                "username": "MrsTurtle",
                "email": "mrsturtle@test.com",
                "image_url" : "/static/images/default-pic.png",
                "header_image_url" : "/static/images/warbler-hero.jpg",
                "bio" : "I am Mrs Turtle",
                "location" : "Florida",
                "password" : "THIS_PASSWORD_IS_WRONG"
                }

            # attempt an edit with an incorrect password
            resp = c.post('/users/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Edit Your Profile.</h2>""", html)

            # logout, then try to get the edit form
            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

            resp = c.get('/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)


    def test_user_delete(self):
        """Test delete user."""
        
        with app.test_client() as c:
        
            data = {
                    "username": "MrsTurtle",
                    "password": "TEST_PASSWORD",
                    }

            # login, delete the user's profile
            c.post('/login', data=data)

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Join Warbler today.</h2>""", html)
            
            # attempt to delete without logging in again
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)



