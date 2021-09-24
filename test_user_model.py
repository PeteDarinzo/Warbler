"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up after tests."""
        
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):

        test_u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(test_u)
        db.session.commit()
        self.id = test_u.id

        res = test_u.__repr__()

        self.assertEqual(f'<User #{self.id}: {test_u.username}, {test_u.email}>', res)


    def test_is_following(self):

        user1 = User(
            email="testuser1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(user1)
        db.session.commit()

        user2 = User(
            email="testuser2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(user2)
        db.session.commit()

        # is user1 following user2?
        res = user1.is_following(user2)

        self.assertFalse(res)

        test_follow = Follows(user_being_followed_id=user2.id, user_following_id=user1.id)

        db.session.add(test_follow)
        db.session.commit()

        # is user1 following user2?
        res = user1.is_following(user2)

        self.assertTrue(res)

    def test_is_followed_by(self):

        user1 = User(
            email="testuser1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(user1)
        db.session.commit()

        user2 = User(
            email="testuser2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(user2)
        db.session.commit()

        # is user1 following user2?
        res = user1.is_followed_by(user2)

        self.assertFalse(res)

        test_follow = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)

        db.session.add(test_follow)
        db.session.commit()

        # is user2 following user1?
        res = user1.is_followed_by(user2)

        self.assertTrue(res)

    def test_signup(self):

        user = User.signup(
                username="JohnnyTest",
                password="TEST_PASSWORD",
                email="johnny@test.com",
                image_url="/static/images/smile.png",
            )
        
        db.session.commit()

        self.assertEqual(f'<User #{user.id}: {user.username}, {user.email}>', str(user))

        User.signup(
                username=None,
                password="TEST_PASSWORD",
                email="test1@test.com",
                image_url="/static/images/smile.png",
            )

        # can a null username be added?
        with self.assertRaises(IntegrityError):
            
            db.session.commit()

        # rollback between tests
        db.session.rollback()

        User.signup(
                username="JohnnyTest",
                password="TEST_PASSWORD",
                email="test2@test.com",
                image_url="/static/images/smile.png",
        )

        # can a duplicate username be added?
        with self.assertRaises(IntegrityError):
            
            db.session.commit()

    def test_user_authenticate(self):

        user = User.signup(
                username="JohnnyTest",
                password="TEST_PASSWORD",
                email="johnny@test.com",
                image_url="/static/images/smile.png",
            )
        
        db.session.commit()

        auth_user = User.authenticate("JohnnyTest", "TEST_PASSWORD")

        self.assertEqual(f'<User #{user.id}: {user.username}, {user.email}>', str(auth_user))


        self.assertFalse(User.authenticate("JoeyTest", "TEST_PASSWORD"))
       
        self.assertFalse(User.authenticate("JohnnyTest", "THE_WRONG_TEST_PASSWORD"))




