import unittest
from unittest.mock import MagicMock

from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.repository.user_repo import UserRepository


class TestUserRepositoryGetUserById(unittest.TestCase):
    def test_get_user_by_id(self):
        user_item = {"ID": "1", "Email": "foo@example.com", "PasswordHash": "p", "Username": "Foo", "Subscription": "std"}
        items = {("USER#1", "PROFILE"): user_item}
        table = MagicMock()
        table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = UserRepository(dynamo)

        cases = [
            {"name": "found", "user_id": "1", "raises": None},
            {"name": "missing", "user_id": "2", "raises": WebException},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        repo.get_user_by_id(case["user_id"])
                    self.assertEqual(ErrorCodes.USER_NOT_FOUND, ctx.exception.error_code)
                else:
                    user = repo.get_user_by_id(case["user_id"])
                    self.assertIsInstance(user, User)
                    self.assertEqual("foo@example.com", user.email)


class TestUserRepositoryGetUserByEmail(unittest.TestCase):
    def test_get_user_by_email(self):
        user_item = {"ID": "1", "Email": "foo@example.com", "PasswordHash": "p", "Username": "Foo", "Subscription": "std"}
        items = {
            ("LOOKUP", "EMAIL#foo@example.com"): {"ID": "1"},
            ("USER#1", "PROFILE"): user_item,
        }
        table = MagicMock()
        table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = UserRepository(dynamo)

        cases = [
            {"name": "found", "email": "foo@example.com", "raises": None},
            {"name": "missing", "email": "bar@example.com", "raises": WebException},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        repo.get_user_by_email(case["email"])
                    self.assertEqual(ErrorCodes.USER_NOT_FOUND, ctx.exception.error_code)
                else:
                    user = repo.get_user_by_email(case["email"])
                    self.assertEqual("1", user.id)


class TestUserRepositoryAddUser(unittest.TestCase):
    def test_add_user(self):
        table = MagicMock()
        client = MagicMock()
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        dynamo.meta.client = client
        repo = UserRepository(dynamo)

        repo.add_user(User(ID="2", Email="bar@example.com", PasswordHash="hash", Username="Bar"))

        client.transact_write_items.assert_called_once()
        call_kwargs = client.transact_write_items.call_args.kwargs
        self.assertEqual(2, len(call_kwargs["TransactItems"]))


class TestUserRepositorySetUserSubscription(unittest.TestCase):
    def test_set_user_subscription(self):
        table = MagicMock()
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = UserRepository(dynamo)

        repo.set_user_subscription(user_id="abc", subscription=Subscription.PREMIUM)

        table.update_item.assert_called_once()
        kwargs = table.update_item.call_args.kwargs
        self.assertEqual(Subscription.PREMIUM.value, kwargs["ExpressionAttributeValues"][":subscription"])


if __name__ == "__main__":
    unittest.main()
