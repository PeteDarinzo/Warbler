"""Message model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follows


# set an evironmental variable
# to use a different database for tests
# before importing app

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

# create tables 

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""


    def setUp(self):
        """Create test client, add sample data"""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def tearDown(self):
        """Clean up after tests."""

        db.session.rollback()


    def test_message_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        m = Message(
            text="This is a test message.",
            timestamp="2016-12-06 23:13:29.694274",
            user_id=u.id
        )

        db.session.add(m)
        db.session.commit()

        user = m.user

        self.assertEqual(f"<User #{u.id}: {u.username}, {u.email}>", str(user))

 