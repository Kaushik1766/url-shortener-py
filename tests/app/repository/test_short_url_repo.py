import unittest
from unittest.mock import MagicMock

from app.errors.web_errors import ErrorCodes, WebException
from app.models.short_url import ShortUrl
from app.repository.short_url_repo import ShortURLRepository


class TestShortURLRepositoryGetUrl(unittest.TestCase):
    def test_get_url(self):
        items = {("SHORTURL#abc", "DETAILS"): {"URL": "example.com"}}
        table = MagicMock()
        table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = ShortURLRepository(dynamo)

        cases = [
            {"name": "found", "short": "abc", "expect": "example.com", "raises": None},
            {"name": "not found", "short": "missing", "expect": None, "raises": WebException},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        repo.get_url(case["short"])
                    self.assertEqual(ErrorCodes.SHORTURL_NOT_FOUND, ctx.exception.error_code)
                else:
                    self.assertEqual(case["expect"], repo.get_url(case["short"]))


class TestShortURLRepositoryGetUrlsByUser(unittest.TestCase):
    def test_get_urls_by_user_id(self):
        table = MagicMock()
        table.query.return_value = {"Items": [{"SK": "SHORTURL#one"}, {"SK": "SHORTURL#two"}]}
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = ShortURLRepository(dynamo)

        result = repo.get_urls_by_user_id("user-1")
        self.assertEqual(["one", "two"], result)


class TestShortURLRepositoryAddUrl(unittest.TestCase):
    def test_add_url(self):
        table = MagicMock()
        client = MagicMock()
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        dynamo.meta.client = client
        repo = ShortURLRepository(dynamo)

        new_url = ShortUrl(ShortURL="stdabc123", ID="1", URL="example.com", CreatedAt=1, OwnerID="user")
        repo.add_url(new_url)

        client.transact_write_items.assert_called_once()
        call_kwargs = client.transact_write_items.call_args.kwargs
        self.assertEqual(2, len(call_kwargs["TransactItems"]))


class TestShortURLRepositoryGetCounter(unittest.TestCase):
    def test_get_counter(self):
        counter = {"val": 5}
        table = MagicMock()

        def _update_item(**kwargs):
            counter["val"] += int(kwargs.get("ExpressionAttributeValues", {}).get(":inc", 0))
            return {"Attributes": {"CurrentCount": counter["val"]}}

        table.update_item.side_effect = _update_item
        dynamo = MagicMock()
        dynamo.Table.return_value = table
        repo = ShortURLRepository(dynamo)

        self.assertEqual(6, repo.get_counter())


if __name__ == "__main__":
    unittest.main()
