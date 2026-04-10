"""Event templates for common AWS Lambda trigger sources."""

from copy import deepcopy
from typing import Any

_TEMPLATE_DESCRIPTIONS: dict[str, str] = {
    "s3": "S3 ObjectCreated:Put event",
    "sqs": "SQS message event (1 record)",
    "sns": "SNS Notification event (1 record)",
    "eventbridge": "EventBridge custom event",
    "apigw": "API Gateway REST API (v1) proxy event",
    "apigw-v2": "API Gateway HTTP API (v2) proxy event",
}

_EVENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "s3": {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2024-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "EXAMPLE"},
                "requestParameters": {"sourceIPAddress": "127.0.0.1"},
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/abc/mnopqrstuvwxyzABCDEFGH",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": "my-bucket",
                        "ownerIdentity": {"principalId": "EXAMPLE"},
                        "arn": "arn:aws:s3:::my-bucket",
                    },
                    "object": {
                        "key": "my-key.txt",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901",
                    },
                },
            }
        ]
    },
    "sqs": {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6reyNurzbEivf...",
                "body": "Hello World",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1703116800000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1703116800001",
                },
                "messageAttributes": {},
                "md5OfBody": "e1d7a5a46cf7a5b9b369eb06f1d26e41",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1",
            }
        ]
    },
    "sns": {
        "Records": [
            {
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789012:Topic:sub",
                "EventSource": "aws:sns",
                "Sns": {
                    "SignatureVersion": "1",
                    "Timestamp": "2024-01-01T00:00:00.000Z",
                    "Signature": "EXAMPLE",
                    "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-abc.pem",
                    "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                    "Message": "Hello World",
                    "MessageAttributes": {
                        "myAttribute": {
                            "Type": "String",
                            "Value": "myValue",
                        }
                    },
                    "Type": "Notification",
                    "UnsubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=...",
                    "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
                    "Subject": "My Subject",
                },
            }
        ]
    },
    "eventbridge": {
        "version": "0",
        "id": "12345678-1234-1234-1234-123456789012",
        "source": "my.custom.source",
        "account": "123456789012",
        "time": "2024-01-01T00:00:00Z",
        "region": "us-east-1",
        "resources": [],
        "detail-type": "MyCustomEvent",
        "detail": {"key": "value"},
    },
    "apigw": {
        "httpMethod": "GET",
        "path": "/hello",
        "resource": "/hello",
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "headers": {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Host": "api.example.com",
        },
        "multiValueHeaders": {
            "Accept": ["application/json"],
        },
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "1234567890",
            "authorizer": None,
            "domainName": "1234567890.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "1234567890",
            "extendedRequestId": "abc123def456=",
            "httpMethod": "GET",
            "identity": {
                "accessKey": None,
                "accountId": None,
                "caller": None,
                "cognitoAuthenticationProvider": None,
                "cognitoAuthenticationType": None,
                "cognitoIdentityId": None,
                "cognitoIdentityPoolId": None,
                "principalOrgId": None,
                "sourceIp": "127.0.0.1",
                "user": None,
                "userAgent": "Custom User Agent String",
                "userArn": None,
            },
            "path": "/hello",
            "protocol": "HTTP/1.1",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "requestTime": "01/Jan/2024:00:00:00 +0000",
            "requestTimeEpoch": 1704067200000,
            "resourceId": None,
            "resourcePath": "/hello",
            "stage": "dev",
        },
        "body": None,
        "isBase64Encoded": False,
    },
    "apigw-v2": {
        "version": "2.0",
        "routeKey": "GET /hello",
        "rawPath": "/hello",
        "rawQueryString": "",
        "cookies": [],
        "headers": {
            "accept": "application/json",
            "content-type": "application/json",
            "host": "api.example.com",
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "api-id",
            "domainName": "api.example.com",
            "domainPrefix": "api",
            "http": {
                "method": "GET",
                "path": "/hello",
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "Custom User Agent",
            },
            "authorizer": None,
            "requestId": "JKJaXmPLvHcESHA=",
            "routeKey": "GET /hello",
            "stage": "$default",
            "time": "01/Jan/2024:00:00:00 +0000",
            "timeEpoch": 1704067200000,
        },
        "body": None,
        "isBase64Encoded": False,
    },
}


def list_templates() -> list[tuple[str, str]]:
    """Return (name, description) pairs for all available event templates."""
    return [(name, _TEMPLATE_DESCRIPTIONS[name]) for name in _EVENT_TEMPLATES]


def get_template(name: str) -> dict[str, Any]:
    """Return a deep copy of the named AWS event template.

    Args:
        name: Template name (e.g. 's3', 'sqs', 'apigw-v2').

    Returns:
        A copy of the event template dict.

    Raises:
        ValueError: If the template name is not recognized.
    """
    if name not in _EVENT_TEMPLATES:
        available = ", ".join(_EVENT_TEMPLATES)
        raise ValueError(f"Unknown template: {name!r}. Available: {available}")
    return deepcopy(_EVENT_TEMPLATES[name])
