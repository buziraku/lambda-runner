"""Tests for the CLI commands."""

from typer.testing import CliRunner

from lambdarunner.cli import app

runner = CliRunner()


class TestVersionFlag:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "lambdarunner" in result.output

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "lambdarunner" in result.output


class TestTemplateCommand:
    def test_no_args_lists_all_types(self):
        result = runner.invoke(app, ["template"])
        assert result.exit_code == 0
        for event_type in ("s3", "sqs", "sns", "eventbridge", "apigw", "apigw-v2"):
            assert event_type in result.output

    def test_no_args_shows_descriptions(self):
        result = runner.invoke(app, ["template"])
        assert result.exit_code == 0
        assert "S3" in result.output
        assert "SQS" in result.output

    def test_s3_shows_json(self):
        result = runner.invoke(app, ["template", "s3"])
        assert result.exit_code == 0
        assert "aws:s3" in result.output
        assert "ObjectCreated:Put" in result.output

    def test_sqs_shows_json(self):
        result = runner.invoke(app, ["template", "sqs"])
        assert result.exit_code == 0
        assert "aws:sqs" in result.output

    def test_sns_shows_json(self):
        result = runner.invoke(app, ["template", "sns"])
        assert result.exit_code == 0
        assert "aws:sns" in result.output

    def test_eventbridge_shows_json(self):
        result = runner.invoke(app, ["template", "eventbridge"])
        assert result.exit_code == 0
        assert "detail-type" in result.output

    def test_apigw_shows_json(self):
        result = runner.invoke(app, ["template", "apigw"])
        assert result.exit_code == 0
        assert "httpMethod" in result.output

    def test_apigw_v2_shows_json(self):
        result = runner.invoke(app, ["template", "apigw-v2"])
        assert result.exit_code == 0
        assert "routeKey" in result.output
        assert "2.0" in result.output

    def test_unknown_type_exits_with_error(self):
        result = runner.invoke(app, ["template", "unknown-source"])
        assert result.exit_code == 1

    def test_unknown_type_shows_error_message(self):
        result = runner.invoke(app, ["template", "kinesis"])
        assert result.exit_code == 1
        assert "Unknown template" in result.output or "kinesis" in result.output
