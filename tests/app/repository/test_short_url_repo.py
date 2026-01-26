import unittest
from unittest.mock import MagicMock

from app.errors.web_errors import ErrorCodes, WebException
from app.models.short_url import ShortUrl
from app.repository.short_url_repo import ShortURLRepository


class TestShortURLRepository(unittest.TestCase):
    def setUp(self):
        self.mock_table = MagicMock()
        self.mock_client = MagicMock()
        self.mock_dynamo = MagicMock()
        self.mock_dynamo.Table.return_value = self.mock_table
        self.mock_dynamo.meta.client = self.mock_client
        self.repo = ShortURLRepository(self.mock_dynamo)

    def tearDown(self):
        pass

    def test_get_url(self):
        items = {("SHORTURL#abc", "DETAILS"): {"URL": "example.com"}}
        self.mock_table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}

        cases = [
            {"name": "found", "short": "abc", "expect": "example.com", "raises": None},
            {"name": "not found", "short": "missing", "expect": None, "raises": WebException},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        self.repo.get_url(case["short"])
                    self.assertEqual(ErrorCodes.SHORTURL_NOT_FOUND, ctx.exception.error_code)
                else:
                    self.assertEqual(case["expect"], self.repo.get_url(case["short"]))

    def test_get_urls_by_user_id(self):
        cases = [
            {
                "name": "returns user urls",
                "query_return": {"Items": [{"SK": "SHORTURL#one"}, {"SK": "SHORTURL#two"}]},
                "user_id": "user-1",
                "expect": ["one", "two"],
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_table.query.return_value = case["query_return"]
                result = self.repo.get_urls_by_user_id(case["user_id"])
                self.assertEqual(case["expect"], result)

    def test_add_url(self):
        cases = [
            {
                "name": "adds url with transaction",
                "url": ShortUrl(ShortURL="stdabc123", ID="1", URL="example.com", CreatedAt=1, OwnerID="user"),
                "expect_items_count": 2,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.repo.add_url(case["url"])
                self.mock_client.transact_write_items.assert_called()
                call_kwargs = self.mock_client.transact_write_items.call_args.kwargs
                self.assertEqual(case["expect_items_count"], len(call_kwargs["TransactItems"]))

    def test_get_counter(self):
        cases = [
            {
                "name": "increments counter",
                "initial_val": 5,
                "expect": 6,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                counter = {"val": case["initial_val"]}

                def _update_item(**kwargs):
                    counter["val"] += int(kwargs.get("ExpressionAttributeValues", {}).get(":inc", 0))
                    return {"Attributes": {"CurrentCount": counter["val"]}}

                self.mock_table.update_item.side_effect = _update_item
                result = self.repo.get_counter()
                self.assertEqual(case["expect"], result)


if __name__ == "__main__":
    unittest.main()
