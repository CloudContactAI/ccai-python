"""
Tests for the Contact Validator service: email validation with Amazon SES.

The responses in tests/fixtures/contact_validator were recorded from the contact-validator API.

:license: MIT
:copyright: 2026 CloudContactAI LLC
"""

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from ccai_python import CCAI, EmailValidationChecks, EmailValidationResult
from ccai_python.ccai import APIError

FIXTURES = Path(__file__).parent / "fixtures" / "contact_validator"


def recorded(name):
    """A response recorded from the API"""
    return json.loads((FIXTURES / f"{name}.json").read_text())


def http_response(status_code, body):
    """What requests returns: the body for a 2xx, an HTTPError from raise_for_status otherwise"""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = body
    response.text = json.dumps(body)
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


class TestEmailValidation(unittest.TestCase):
    """Email validation results carry the verdict, the six checks, the date and whether the result was reused"""

    def setUp(self):
        self.ccai = CCAI(client_id="<client_id>", api_key="<api_key>")

    def validate_email(self, name, email="jane@example.com"):
        with patch("ccai_python.ccai.requests.request", return_value=http_response(200, recorded(name))) as request:
            result = self.ccai.contact_validator.validate_email(email)
        return result, request

    def test_posts_the_address_to_the_email_endpoint(self):
        _, request = self.validate_email("email-valid")

        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertTrue(kwargs["url"].endswith("/v1/contact-validator/email"))
        self.assertEqual(kwargs["json"], {"email": "jane@example.com"})

    def test_returns_the_verdict_the_six_checks_the_date_and_reused(self):
        result, _ = self.validate_email("email-valid")

        self.assertIsInstance(result, EmailValidationResult)
        self.assertEqual(result.status, "valid")
        self.assertTrue(result.metadata["safe_to_send"])
        self.assertEqual(result.metadata["ai_verdict"], "valid")
        self.assertEqual(result.verdict, "HIGH")
        self.assertIsInstance(result.checks, EmailValidationChecks)
        self.assertEqual(
            result.checks.model_dump(),
            {
                "hasValidSyntax": "HIGH",
                "hasValidDnsRecords": "HIGH",
                "mailboxExists": "HIGH",
                "isRoleAddress": "LOW",
                "isDisposable": "LOW",
                "isRandomInput": "LOW",
            },
        )
        self.assertEqual(result.validatedAt, "2026-11-13T15:02:11Z")
        self.assertIs(result.reused, False)

    def test_the_fields_are_also_in_the_metadata(self):
        result, _ = self.validate_email("email-valid")

        self.assertEqual(result.metadata["verdict"], "HIGH")
        self.assertEqual(result.metadata["checks"]["mailboxExists"], "HIGH")
        self.assertEqual(result.metadata["validatedAt"], "2026-11-13T15:02:11Z")
        self.assertIs(result.metadata["reused"], False)

    def test_says_when_the_result_is_a_saved_check(self):
        result, _ = self.validate_email("email-reused")
        self.assertIs(result.reused, True)

    def test_a_disposable_address_is_risky(self):
        result, _ = self.validate_email("email-risky-disposable", "temp@mailinator.com")

        self.assertEqual(result.status, "risky")
        self.assertFalse(result.metadata["safe_to_send"])
        self.assertEqual(result.checks.isDisposable, "HIGH")

    def test_a_low_address_is_invalid(self):
        result, _ = self.validate_email("email-invalid-low", "nobody@no-such-domain-example.xyz")

        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.verdict, "LOW")
        self.assertEqual(result.checks.hasValidDnsRecords, "LOW")

    def test_an_address_rejected_before_asking_ses_has_unknown_checks_no_date_and_the_reason(self):
        result, _ = self.validate_email("email-rejected-format", "not-an-email")

        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.verdict, "UNKNOWN")
        self.assertEqual(set(result.checks.model_dump().values()), {"UNKNOWN"})
        self.assertIsNone(result.validatedAt)
        self.assertEqual(result.metadata["error"], "Invalid email format")

    def test_a_response_without_the_new_fields_is_read_as_before(self):
        result, _ = self.validate_email("email-legacy")

        self.assertEqual(result.status, "valid")
        self.assertTrue(result.metadata["safe_to_send"])
        self.assertEqual(result.metadata["ai_verdict"], "Mode: Sandbox")
        self.assertIsNone(result.verdict)
        self.assertIsNone(result.checks)
        self.assertIsNone(result.validatedAt)
        self.assertIsNone(result.reused)

    def test_the_result_still_dumps_as_it_always_did(self):
        result, _ = self.validate_email("email-valid")
        self.assertEqual(set(result.model_dump().keys()), {"contactField", "type", "status", "metadata"})

    def test_403_when_email_validation_is_not_enabled_for_the_account(self):
        with patch("ccai_python.ccai.requests.request", return_value=http_response(403, recorded("error-403"))):
            with self.assertRaises(APIError) as caught:
                self.ccai.contact_validator.validate_email("jane@example.com")

        self.assertEqual(caught.exception.status_code, 403)
        self.assertIn("Email validation is not enabled for this account", caught.exception.message)

    def test_502_when_ses_rejects_the_check_with_the_message_from_aws(self):
        with patch("ccai_python.ccai.requests.request", return_value=http_response(502, recorded("error-502"))):
            with self.assertRaises(APIError) as caught:
                self.ccai.contact_validator.validate_email("jane@example.com")

        self.assertEqual(caught.exception.status_code, 502)
        self.assertIn("ses:GetEmailAddressInsights", caught.exception.message)


class TestBulkEmailValidation(unittest.TestCase):
    def setUp(self):
        self.ccai = CCAI(client_id="<client_id>", api_key="<api_key>")
        self.emails = ["jane@example.com", "temp@mailinator.com", "bad@example.com"]

    def validate_emails(self):
        with patch("ccai_python.ccai.requests.request", return_value=http_response(200, recorded("emails-bulk"))) as request:
            bulk = self.ccai.contact_validator.validate_emails(self.emails)
        return bulk, request

    def test_posts_the_addresses_to_the_bulk_endpoint(self):
        _, request = self.validate_emails()

        kwargs = request.call_args.kwargs
        self.assertTrue(kwargs["url"].endswith("/v1/contact-validator/emails"))
        self.assertEqual(kwargs["json"], {"emails": self.emails})

    def test_every_result_has_the_new_fields_and_the_summary_is_as_before(self):
        bulk, _ = self.validate_emails()

        self.assertEqual(bulk.summary.model_dump(), {"total": 3, "valid": 1, "invalid": 1, "risky": 1, "landline": 0})
        reused, risky, _failed = bulk.results
        self.assertIs(reused.reused, True)
        self.assertEqual(reused.verdict, "HIGH")
        self.assertEqual(risky.verdict, "MEDIUM")
        self.assertEqual(risky.checks.isDisposable, "HIGH")
        self.assertEqual(risky.validatedAt, "2026-11-13T15:05:40Z")

    def test_an_address_ses_failed_to_check_is_invalid_with_the_reason_and_none_of_the_new_fields(self):
        bulk, _ = self.validate_emails()

        failed = bulk.results[2]
        self.assertEqual(failed.status, "invalid")
        self.assertEqual(failed.metadata["error"], "The domain is not allowed")
        self.assertIsNone(failed.verdict)
        self.assertIsNone(failed.checks)

    def test_403_when_email_validation_is_not_enabled_for_the_account(self):
        with patch("ccai_python.ccai.requests.request", return_value=http_response(403, recorded("error-403"))):
            with self.assertRaises(APIError) as caught:
                self.ccai.contact_validator.validate_emails(self.emails)
        self.assertEqual(caught.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
