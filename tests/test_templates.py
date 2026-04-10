"""Tests for the event templates module."""

import pytest

from lambdarunner.templates import get_template, list_templates


class TestListTemplates:
    def test_returns_expected_keys(self):
        names = [name for name, _ in list_templates()]
        assert "s3" in names
        assert "sqs" in names
        assert "sns" in names
        assert "eventbridge" in names
        assert "apigw" in names
        assert "apigw-v2" in names

    def test_returns_six_templates(self):
        assert len(list_templates()) == 6

    def test_all_descriptions_non_empty(self):
        for name, description in list_templates():
            assert description, f"Template {name!r} has empty description"


class TestGetTemplate:
    def test_s3_structure(self):
        t = get_template("s3")
        assert "Records" in t
        record = t["Records"][0]
        assert record["eventSource"] == "aws:s3"
        assert record["eventName"] == "ObjectCreated:Put"
        assert "bucket" in record["s3"]
        assert "object" in record["s3"]

    def test_sqs_structure(self):
        t = get_template("sqs")
        assert "Records" in t
        record = t["Records"][0]
        assert record["eventSource"] == "aws:sqs"
        assert "body" in record
        assert "messageId" in record

    def test_sns_structure(self):
        t = get_template("sns")
        assert "Records" in t
        record = t["Records"][0]
        assert record["EventSource"] == "aws:sns"
        assert "Sns" in record
        assert record["Sns"]["Type"] == "Notification"

    def test_eventbridge_structure(self):
        t = get_template("eventbridge")
        assert "version" in t
        assert "source" in t
        assert "detail-type" in t
        assert "detail" in t
        assert t["version"] == "0"

    def test_apigw_structure(self):
        t = get_template("apigw")
        assert "httpMethod" in t
        assert "path" in t
        assert "requestContext" in t
        assert t["httpMethod"] == "GET"

    def test_apigw_v2_structure(self):
        t = get_template("apigw-v2")
        assert t["version"] == "2.0"
        assert "routeKey" in t
        assert "rawPath" in t
        assert "requestContext" in t

    def test_returns_deep_copy(self):
        t1 = get_template("s3")
        t1["Records"][0]["eventSource"] = "mutated"
        t2 = get_template("s3")
        assert t2["Records"][0]["eventSource"] == "aws:s3"

    def test_unknown_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("unknown-source")

    def test_unknown_error_lists_available(self):
        with pytest.raises(ValueError, match="s3"):
            get_template("invalid")
