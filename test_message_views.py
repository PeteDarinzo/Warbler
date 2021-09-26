"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

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


class MessageViewTestCase(TestCase):
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


    def test_add_message(self):
        """Can a user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of our tests

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

        # logout user, then try to add a message
        with self.client as c:
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            html = resp.get_data(as_text=True)

            # test that user is redirected to ('/')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)
            

    def test_view_message(self):
        """Test that a message can be viewed"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            c.post("/messages/new", data={"text": "Hello"})

            m_id = Message.query.one().id
        
            resp = c.get(f"/messages/{m_id}")

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<p class="single-message">Hello</p>""", html)

        # logout user, then try to view a message, which can be done
        with self.client as c:
                with c.session_transaction() as sess:
                    del sess[CURR_USER_KEY]

                resp = c.get(f"/messages/{m_id}")

                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("""<p class="single-message">Hello</p>""", html)


    def test_delete_message(self):
        """Test that a message can be deleted."""


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # post a new message
            c.post("/messages/new", data={"text": "Hello"})
            m_id = Message.query.one().id

            # delete message
            resp = c.post(f"/messages/{m_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # make sure user is redirected
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"""<h4 id="sidebar-username">@{self.testuser.username}</h4>""", html)

            # make sure message was deleted
            self.assertEqual(Message.query.all(), [])

            # make a new message
            c.post("/messages/new", data={"text": "Hello Again"})
            m_id = Message.query.one().id

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"""<h4 id="sidebar-username">@{self.testuser.username}</h4>""", html)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
        # log in new user, and attempt to delete the message
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id
            
            resp = c.post(f"/messages/{m_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # make sure user is redirected
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<aside class="col-md-4 col-lg-3 col-sm-12" id="home-aside">""", html)

            # check that the message still exists
            self.assertEqual(Message.query.one().id, m_id)

        # logout user, then try to delete a message
        with self.client as c:
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]

            resp = c.post(f"/messages/{m_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

            # make sure message wasn't deleted
            self.assertEqual(Message.query.one().id, m_id)

        
        


    def test_like_message(self):
        """Test that a message can be liked."""

        # login a user, then make post a message
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            c.post("/messages/new", data={"text": "Hello"})
            m_id = Message.query.one().id

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
        # log in new user, and like the message
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.post(f"/users/add_like/{m_id}", follow_redirects=True)
            data = resp.json

            self.assertEqual({"message" : f"Message number {m_id} liked"}, data)
            self.assertEqual(resp.status_code, 200)
            
        # logout user, then try to like a message
        with self.client as c:
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
            
            resp = c.post(f"/users/add_like/{m_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("""<h2 class="join-message">Welcome back.</h2>""", html)

        