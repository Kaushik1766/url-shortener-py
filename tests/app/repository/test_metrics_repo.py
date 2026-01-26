import unittest

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

    def test_save_metrics_insert_then_update(self):
        table = _FakeTable(put_error_code="ConditionalCheckFailedException")
        repo = MetricsRepository(_FakeDB(table))

        failed = repo.save_metrics([self.sample_metric])

        self.assertEqual([], failed)
        self.assertEqual(1, len(table.put_calls))
        self.assertEqual(1, len(table.update_calls))
        update = table.update_calls[0]
        self.assertEqual("SHORTURL#abc", update["Key"]["PK"])
        self.assertIn("ByCountry", update["UpdateExpression"])

    def test_save_metrics_non_conditional_error_returns_failed(self):
        table = _FakeTable(put_error_code="Other")
        repo = MetricsRepository(_FakeDB(table))

        failed = repo.save_metrics([self.sample_metric])

        self.assertEqual(["m1", "m2"], failed)
        self.assertEqual(0, len(table.update_calls))

    def test_get_url_metrics_empty(self):
        table = _FakeTable(query_items=[])
        repo = MetricsRepository(_FakeDB(table))

        self.assertEqual([], repo.get_url_metrics("2023-01-01", "2023-01-02", "abc"))

    def test_get_url_metrics_items(self):
        item = self.sample_metric.model_dump(by_alias=True)
        table = _FakeTable(query_items=[item])
        repo = MetricsRepository(_FakeDB(table))

        result = repo.get_url_metrics("2023-01-01", "2023-01-02", "abc")
        self.assertEqual(1, len(result))
        self.assertEqual("abc", result[0].short_url)


if __name__ == "__main__":
    unittest.main()
