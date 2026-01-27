import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from app.models.metrics import DailyAccessMetrics
from app.repository.metrics_repo import MetricsRepository


class _FakeTable:
    def __init__(self, put_error_code=None, query_items=None):
        self.put_calls = []
        self.update_calls = []
        self.query_items = query_items or []
        self.put_error_code = put_error_code

    def put_item(self, **kwargs):
        self.put_calls.append(kwargs)
        if self.put_error_code:
            raise ClientError(
                {
                    "Error": {
                        "Code": self.put_error_code,
                        "Message": "boom",
                    }
                },
                "PutItem",
            )
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def update_item(self, **kwargs):
        self.update_calls.append(kwargs)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(self, **kwargs):
        return {"Items": self.query_items}


class _FakeDB:
    def __init__(self, table: _FakeTable):
        self._table = table
        self.meta = type("meta", (), {"client": None})

    def Table(self, name):
        return self._table


class TestMetricsRepository(unittest.TestCase):
    def setUp(self):
        self.sample_metric = DailyAccessMetrics(
            ShortURL="abc",
            Day="2023-01-01",
            TotalHits=2,
            ByCountry={"IN": 2},
            ByDeviceType={"desktop": 1, "mobile": 1},
            ByReferrer={"ref": 2},
            message_ids=["m1", "m2"],
        )
        self.mock_table = MagicMock()
        self.mock_db = MagicMock()
        self.mock_db.Table.return_value = self.mock_table
        self.mock_db.meta = type("meta", (), {"client": None})

    def tearDown(self):
        pass

    def test_save_metrics(self):
        cases = [
            {
                "name": "insert then update on conditional failure",
                "put_error_code": "ConditionalCheckFailedException",
                "expect_failed": [],
                "expect_update_calls": 1,
            },
            {
                "name": "non conditional error returns failed",
                "put_error_code": "Other",
                "expect_failed": ["m1", "m2"],
                "expect_update_calls": 0,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                table = _FakeTable(put_error_code=case["put_error_code"])
                repo = MetricsRepository(_FakeDB(table))

                failed = repo.save_metrics([self.sample_metric])

                self.assertEqual(case["expect_failed"], failed)
                self.assertEqual(case["expect_update_calls"], len(table.update_calls))

    def test_get_url_metrics(self):
        cases = [
            {
                "name": "empty results",
                "query_items": [],
                "expect_count": 0,
            },
            {
                "name": "returns items",
                "query_items": [self.sample_metric.model_dump(by_alias=True)],
                "expect_count": 1,
                "expect_short_url": "abc",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                table = _FakeTable(query_items=case["query_items"])
                repo = MetricsRepository(_FakeDB(table))

                result = repo.get_url_metrics("2023-01-01", "2023-01-02", "abc")

                self.assertEqual(case["expect_count"], len(result))
                if "expect_short_url" in case:
                    self.assertEqual(case["expect_short_url"], result[0].short_url)


if __name__ == "__main__":
    unittest.main()
