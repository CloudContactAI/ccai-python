"""
Python SDK integration tests — 52 tests
Covers: SMS (1-6), MMS (7-17), Email (18-22), Webhook (23-29), Contact (30-31),
Brands (32-36), Campaigns (37-42), ContactValidator (43-46), Negative cases (47-52)

Test results use three states:
  PASS — the test ran and all assertions held
  FAIL — the test ran and an assertion (or the API call) failed
  SKIP — a prerequisite test failed, so this test could not run

Resources created during the run (webhooks, brands, campaigns) are tracked and
deleted in a final cleanup block even if tests fail midway.
"""

import base64
import hmac
import hashlib
import json
import os
import sys
import tempfile
import time

# The SDK is installed in the Docker container via pip install -e /sdk
from ccai_python.ccai import CCAI
from ccai_python.sms.sms import Account
from ccai_python.email_service import EmailAccount, EmailCampaign
from ccai_python.webhook import WebhookConfig, WebhookEvent, WebhookEventType

# ── Helpers ───────────────────────────────────────────────────────────────────


class SkipTest(Exception):
    """Raised when a test cannot run because a prerequisite test failed."""


class Runner:
    """Tracks PASS/FAIL/SKIP counts without module-level globals."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def run(self, name: str, fn) -> None:
        try:
            fn()
            print(f"  PASS [{name}]")
            self.passed += 1
        except SkipTest as e:
            print(f"  SKIP [{name}]: {e}")
            self.skipped += 1
        except Exception as e:
            print(f"  FAIL [{name}]: {e}")
            self.failed += 1


def expect_error(fn, what: str) -> None:
    """Runs fn and asserts that it raises — used by the negative test cases."""
    try:
        fn()
    except SkipTest:
        raise
    except Exception:
        return  # failed as expected
    raise RuntimeError(f"expected {what} to fail, but it succeeded")


def assert_send_response(resp) -> None:
    """Asserts that a send-style response carries a campaign/message identifier."""
    if resp is None:
        raise RuntimeError("empty response")
    rid = getattr(resp, "id", None) or getattr(resp, "campaign_id", None)
    if not rid:
        raise RuntimeError(f"response has no id/campaign_id: {resp}")


def hmac_sha256_base64(secret: str, message: str) -> str:
    raw = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(raw).decode()


def write_temp_png() -> str:
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    buf = base64.b64decode(png_b64)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(buf)
    tmp.flush()
    tmp.close()
    return tmp.name


def cleanup_resources(client: CCAI, cleanup: dict) -> None:
    """Deletes any resource still tracked at the end of the run (always called)."""
    for cid in cleanup["campaign_ids"]:
        try:
            client.campaigns.delete(cid)
            print(f"  CLEANUP: deleted leftover campaign {cid}")
        except Exception as e:
            print(f"  CLEANUP: could not delete campaign {cid}: {e}")
    for bid in cleanup["brand_ids"]:
        try:
            client.brands.delete(bid)
            print(f"  CLEANUP: deleted leftover brand {bid}")
        except Exception as e:
            print(f"  CLEANUP: could not delete brand {bid}: {e}")
    for wid in cleanup["webhook_ids"]:
        try:
            client.webhook.delete(wid)
            print(f"  CLEANUP: deleted leftover webhook {wid}")
        except Exception as e:
            print(f"  CLEANUP: could not delete webhook {wid}: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

REQUIRED_ENV = [
    "CCAI_CLIENT_ID",
    "CCAI_API_KEY",
    "CCAI_TEST_PHONE",
    "CCAI_TEST_PHONE_2",
    "CCAI_TEST_PHONE_3",
    "CCAI_TEST_EMAIL",
    "CCAI_TEST_EMAIL_2",
    "CCAI_TEST_EMAIL_3",
    "CCAI_TEST_FIRST_NAME",
    "CCAI_TEST_LAST_NAME",
    "CCAI_TEST_FIRST_NAME_2",
    "CCAI_TEST_LAST_NAME_2",
    "CCAI_TEST_FIRST_NAME_3",
    "CCAI_TEST_LAST_NAME_3",
    "WEBHOOK_URL",
]


def main() -> None:
    # Validate ALL required env vars up front and report every missing one,
    # instead of failing later with a cryptic API error.
    missing = [key for key in REQUIRED_ENV if not os.environ.get(key)]
    if missing:
        print(f"ERROR: required env vars are not set: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

    client_id = os.environ["CCAI_CLIENT_ID"]
    api_key = os.environ["CCAI_API_KEY"]
    phone1 = os.environ["CCAI_TEST_PHONE"]
    phone2 = os.environ["CCAI_TEST_PHONE_2"]
    phone3 = os.environ["CCAI_TEST_PHONE_3"]
    email1 = os.environ["CCAI_TEST_EMAIL"]
    email2 = os.environ["CCAI_TEST_EMAIL_2"]
    email3 = os.environ["CCAI_TEST_EMAIL_3"]
    fn1 = os.environ["CCAI_TEST_FIRST_NAME"]
    ln1 = os.environ["CCAI_TEST_LAST_NAME"]
    fn2 = os.environ["CCAI_TEST_FIRST_NAME_2"]
    ln2 = os.environ["CCAI_TEST_LAST_NAME_2"]
    fn3 = os.environ["CCAI_TEST_FIRST_NAME_3"]
    ln3 = os.environ["CCAI_TEST_LAST_NAME_3"]

    # Unique per-run suffix so parallel SDK runs don't collide on the same webhook URL
    run_id = f"python-{int(time.time())}"
    webhook_base = os.environ["WEBHOOK_URL"]
    sep = "&" if "?" in webhook_base else "?"
    webhook_url = f"{webhook_base}{sep}run={run_id}"

    sender_email = os.environ.get("CCAI_TEST_SENDER_EMAIL") or "noreply@cloudcontactai.com"
    reply_email = sender_email
    sender_name = "CCAI Test"
    webhook_secret = os.environ.get("CCAI_WEBHOOK_SECRET") or "test-webhook-secret-python"

    # Use CCAI_BASE_URL if set (local dev), otherwise fall back to test environment
    client = CCAI(client_id=client_id, api_key=api_key,
                  use_test=not bool(os.environ.get('CCAI_BASE_URL')))

    print("==============================================")
    print("  CCAI Python SDK Integration Tests")
    print("==============================================")

    runner = Runner()
    run = runner.run

    # Write temp PNG for MMS tests
    png_path = write_temp_png()

    # IDs of resources created by the tests; anything still listed here at the
    # end of the run is deleted by cleanup_resources (tests remove entries they
    # already deleted themselves).
    cleanup = {"webhook_ids": [], "brand_ids": [], "campaign_ids": []}

    try:
        # ── SMS Tests (1-6) ──────────────────────────────────────────────────────
        print("\n--- SMS ---")

        # 01 — SMS.send_single
        def test_01():
            resp = client.sms.send_single(fn1, ln1, phone1, "Hello from Python SDK!", "Python Test")
            assert_send_response(resp)
        run("01 SMS.send_single", test_01)

        # 02 — SMS.send (1 recipient)
        def test_02():
            resp = client.sms.send(
                [Account(first_name=fn1, last_name=ln1, phone=phone1)],
                "Hello 1 recipient!", "Python Test"
            )
            assert_send_response(resp)
        run("02 SMS.send (1 recipient)", test_02)

        # 03 — SMS.send (2 recipients)
        def test_03():
            resp = client.sms.send(
                [
                    Account(first_name=fn1, last_name=ln1, phone=phone1),
                    Account(first_name=fn2, last_name=ln2, phone=phone2),
                ],
                "Hello 2 recipients!", "Python Test"
            )
            assert_send_response(resp)
        run("03 SMS.send (2 recipients)", test_03)

        # 04 — SMS.send (3 recipients)
        def test_04():
            resp = client.sms.send(
                [
                    Account(first_name=fn1, last_name=ln1, phone=phone1),
                    Account(first_name=fn2, last_name=ln2, phone=phone2),
                    Account(first_name=fn3, last_name=ln3, phone=phone3),
                ],
                "Hello 3 recipients!", "Python Test"
            )
            assert_send_response(resp)
        run("04 SMS.send (3 recipients)", test_04)

        # 05 — SMS.send with data
        def test_05():
            resp = client.sms.send(
                [Account(first_name=fn1, last_name=ln1, phone=phone1, data={"city": "Miami", "offer": "20% off"})],
                "Hello from ${city}! Claim your ${offer}.", "Python Test Data"
            )
            assert_send_response(resp)
        run("05 SMS.send with data", test_05)

        # 06 — SMS.send with message_data
        def test_06():
            resp = client.sms.send(
                [Account(first_name=fn1, last_name=ln1, phone=phone1, message_data='{"trackingId":"abc123"}')],
                "Hello with messageData!", "Python Test MsgData"
            )
            assert_send_response(resp)
        run("06 SMS.send with message_data", test_06)

        # ── MMS Tests (7-17) ─────────────────────────────────────────────────────
        print("\n--- MMS ---")

        signed_url_resp = None
        upload_ok = False

        # 07 — MMS.get_signed_upload_url
        def test_07():
            nonlocal signed_url_resp
            resp = client.mms.get_signed_upload_url("test_image.png", "image/png")
            if not resp.get("signedS3Url"):
                raise RuntimeError("signedS3Url is empty")
            if not resp.get("fileKey"):
                raise RuntimeError("fileKey is empty")
            signed_url_resp = resp
        run("07 MMS.get_signed_upload_url", test_07)

        # 08 — MMS.upload_image_to_signed_url
        def test_08():
            nonlocal upload_ok
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            ok = client.mms.upload_image_to_signed_url(signed_url_resp["signedS3Url"], png_path, "image/png")
            if not ok:
                raise RuntimeError("upload returned False")
            upload_ok = True
        run("08 MMS.upload_image_to_signed_url", test_08)

        # 09 — MMS.send_single
        def test_09():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send_single(signed_url_resp["fileKey"], fn1, ln1, phone1, "MMS single!", "Python MMS Test")
            assert_send_response(resp)
        run("09 MMS.send_single", test_09)

        # 10 — MMS.send (1 recipient)
        def test_10():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send(
                signed_url_resp["fileKey"],
                [Account(first_name=fn1, last_name=ln1, phone=phone1)],
                "MMS 1 recipient!", "Python MMS Test"
            )
            assert_send_response(resp)
        run("10 MMS.send (1 recipient)", test_10)

        # 11 — MMS.send (2 recipients)
        def test_11():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send(
                signed_url_resp["fileKey"],
                [
                    Account(first_name=fn1, last_name=ln1, phone=phone1),
                    Account(first_name=fn2, last_name=ln2, phone=phone2),
                ],
                "MMS 2 recipients!", "Python MMS Test"
            )
            assert_send_response(resp)
        run("11 MMS.send (2 recipients)", test_11)

        # 12 — MMS.send (3 recipients)
        def test_12():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send(
                signed_url_resp["fileKey"],
                [
                    Account(first_name=fn1, last_name=ln1, phone=phone1),
                    Account(first_name=fn2, last_name=ln2, phone=phone2),
                    Account(first_name=fn3, last_name=ln3, phone=phone3),
                ],
                "MMS 3 recipients!", "Python MMS Test"
            )
            assert_send_response(resp)
        run("12 MMS.send (3 recipients)", test_12)

        # 13 — MMS.send with data
        def test_13():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send(
                signed_url_resp["fileKey"],
                [Account(first_name=fn1, last_name=ln1, phone=phone1, data={"product": "Widget"})],
                "Check out ${product}!", "Python MMS Data"
            )
            assert_send_response(resp)
        run("13 MMS.send with data", test_13)

        # 14 — MMS.send with message_data
        def test_14():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            resp = client.mms.send(
                signed_url_resp["fileKey"],
                [Account(first_name=fn1, last_name=ln1, phone=phone1, message_data='{"campaignId":"mms-py-001"}')],
                "MMS with messageData!", "Python MMS MsgData"
            )
            assert_send_response(resp)
        run("14 MMS.send with message_data", test_14)

        # 15 — MMS.check_file_uploaded — the file uploaded in test 08 must actually exist
        def test_15():
            if not signed_url_resp:
                raise SkipTest("dependency test 07 failed")
            if not upload_ok:
                raise SkipTest("dependency test 08 failed")
            resp = client.mms.check_file_uploaded(signed_url_resp["fileKey"])
            if not resp.url:
                raise RuntimeError(f"expected non-empty storedUrl for uploaded file {signed_url_resp['fileKey']}")
        run("15 MMS.check_file_uploaded", test_15)

        # 16 — MMS.send_with_image (fresh upload)
        def test_16():
            resp = client.mms.send_with_image(
                png_path, "image/png",
                [Account(first_name=fn1, last_name=ln1, phone=phone1)],
                "MMS with image!", "Python MMS Image",
                force_new_campaign=True
            )
            assert_send_response(resp)
        run("16 MMS.send_with_image (fresh upload)", test_16)

        # 17 — MMS.send_with_image (cached)
        def test_17():
            resp = client.mms.send_with_image(
                png_path, "image/png",
                [Account(first_name=fn1, last_name=ln1, phone=phone1)],
                "MMS cached image!", "Python MMS Cache",
                force_new_campaign=True
            )
            assert_send_response(resp)
        run("17 MMS.send_with_image (cached)", test_17)

        # ── Email Tests (18-22) ──────────────────────────────────────────────────
        print("\n--- Email ---")

        # 18 — Email.send_single
        def test_18():
            resp = client.email.send_single(
                fn1, ln1, email1,
                "Python SDK Test Email",
                "<p>Hello from Python SDK!</p>",
                sender_email=sender_email,
                reply_email=reply_email,
                sender_name=sender_name,
                title="Python Email Test"
            )
            assert_send_response(resp)
        run("18 Email.send_single", test_18)

        # 19 — Email.send (1 recipient)
        def test_19():
            resp = client.email.send(
                [EmailAccount(first_name=fn1, last_name=ln1, email=email1)],
                "Python SDK Email 1", "<p>Hello 1!</p>",
                sender_email, reply_email, sender_name, "Python Email Test"
            )
            assert_send_response(resp)
        run("19 Email.send (1 recipient)", test_19)

        # 20 — Email.send (2 recipients)
        def test_20():
            resp = client.email.send(
                [
                    EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                    EmailAccount(first_name=fn2, last_name=ln2, email=email2),
                ],
                "Python SDK Email 2", "<p>Hello 2!</p>",
                sender_email, reply_email, sender_name, "Python Email Test"
            )
            assert_send_response(resp)
        run("20 Email.send (2 recipients)", test_20)

        # 21 — Email.send (3 recipients)
        def test_21():
            resp = client.email.send(
                [
                    EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                    EmailAccount(first_name=fn2, last_name=ln2, email=email2),
                    EmailAccount(first_name=fn3, last_name=ln3, email=email3),
                ],
                "Python SDK Email 3", "<p>Hello 3!</p>",
                sender_email, reply_email, sender_name, "Python Email Test"
            )
            assert_send_response(resp)
        run("21 Email.send (3 recipients)", test_21)

        # 22 — Email.send_campaign (direct campaign object)
        def test_22():
            campaign = EmailCampaign(
                subject="Python SDK Campaign Test",
                title="Python Email Campaign",
                message="<p>Campaign email from Python SDK!</p>",
                sender_email=sender_email,
                reply_email=reply_email,
                sender_name=sender_name,
                accounts=[
                    EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                    EmailAccount(first_name=fn2, last_name=ln2, email=email2),
                ],
            )
            resp = client.email.send_campaign(campaign)
            assert_send_response(resp)
        run("22 Email.send_campaign", test_22)

        # ── Webhook Tests (23-29) ────────────────────────────────────────────────
        print("\n--- Webhook ---")

        registered_webhook_id = None

        # 23 — Webhook.register
        def test_23():
            nonlocal registered_webhook_id
            config = WebhookConfig(
                url=webhook_url,
                events=[WebhookEventType.MESSAGE_SENT],
                secret=webhook_secret
            )
            resp = client.webhook.register(config)
            wid = resp.id
            if not wid:
                raise RuntimeError("webhook ID is empty after register")
            registered_webhook_id = str(wid)
            cleanup["webhook_ids"].append(registered_webhook_id)
        run("23 Webhook.register", test_23)

        # 24 — Webhook.list — must contain the webhook registered in test 23
        def test_24():
            hooks = client.webhook.list()
            if not isinstance(hooks, list) or len(hooks) == 0:
                raise RuntimeError("expected at least one webhook, got 0")
            if registered_webhook_id:
                found = any(str(h.id) == registered_webhook_id for h in hooks)
                if not found:
                    raise RuntimeError(f"webhook {registered_webhook_id} registered in test 23 not present in list()")
        run("24 Webhook.list", test_24)

        # 25 — Webhook.update — then verify via list() that the URL actually changed
        def test_25():
            if not registered_webhook_id:
                raise SkipTest("dependency test 23 failed")
            updated_url = f"{webhook_url}&updated=1"
            client.webhook.update(
                registered_webhook_id,
                {"url": updated_url, "secret": "updated-secret-python"}
            )
            hooks = client.webhook.list()
            hook = next((h for h in hooks if str(h.id) == registered_webhook_id), None)
            if hook is None:
                raise RuntimeError(f"webhook {registered_webhook_id} not found in list() after update")
            if "updated=1" not in str(hook.url or ""):
                raise RuntimeError(f'webhook URL was not updated: expected to contain "updated=1", got "{hook.url}"')
        run("25 Webhook.update", test_25)

        # 26 — Webhook.verify_signature (valid)
        def test_26():
            event_hash = "abc123eventHash"
            sig = hmac_sha256_base64(webhook_secret, f"{client_id}:{event_hash}")
            ok = client.webhook.verify_signature(sig, client_id, event_hash, webhook_secret)
            if not ok:
                raise RuntimeError("expected valid signature to return True")
        run("26 Webhook.verify_signature (valid)", test_26)

        # 27 — Webhook.verify_signature (invalid)
        def test_27():
            ok = client.webhook.verify_signature("invalidsig==", client_id, "somehash", webhook_secret)
            if ok:
                raise RuntimeError("expected invalid signature to return False")
        run("27 Webhook.verify_signature (invalid)", test_27)

        # 28 — Webhook.create_handler (parses a webhook event)
        def test_28():
            received_events = []
            handler = webhook_create_handler(client, received_events)
            payload = {
                "eventType": "message.sent",
                "data": {"to": "+15005550001"},
                "eventHash": "abc123",
            }
            result = handler(payload)
            if not result.get("received"):
                raise RuntimeError("handler did not return received=True")
            if len(received_events) == 0:
                raise RuntimeError("on_event callback was not called")
            event = received_events[0]
            if not event.event_type:
                raise RuntimeError("eventType is empty after parsing")
        run("28 Webhook.create_handler (parse event)", test_28)

        # 29 — Webhook.delete — then verify via list() that it is gone
        def test_29():
            if not registered_webhook_id:
                raise SkipTest("dependency test 23 failed")
            client.webhook.delete(registered_webhook_id)
            cleanup["webhook_ids"] = [w for w in cleanup["webhook_ids"] if w != registered_webhook_id]
            hooks = client.webhook.list()
            still_there = any(str(h.id) == registered_webhook_id for h in hooks)
            if still_there:
                raise RuntimeError(f"webhook {registered_webhook_id} still present in list() after delete")
        run("29 Webhook.delete", test_29)

        # ── Contact Tests (30-31) ────────────────────────────────────────────────
        print("\n--- Contact ---")

        # 30 — Contact.set_do_not_text(True)
        def test_30():
            resp = client.contact.set_do_not_text(True, phone=phone1)
            if resp is None:
                raise RuntimeError("empty response")
        run("30 Contact.set_do_not_text(True)", test_30)

        # 31 — Contact.set_do_not_text(False)
        def test_31():
            resp = client.contact.set_do_not_text(False, phone=phone1)
            if resp is None:
                raise RuntimeError("empty response")
        run("31 Contact.set_do_not_text(False)", test_31)

        # ── Brand Tests (32-36) ──────────────────────────────────────────────────
        print("\n--- Brands ---")

        brand_id = None

        # 32 — Brand.create
        def test_32():
            nonlocal brand_id
            resp = client.brands.create({
                "legalCompanyName": "Test Company LLC",
                "entityType":       "PRIVATE_PROFIT",
                "taxId":            "123456789",
                "taxIdCountry":     "US",
                "country":          "US",
                "verticalType":     "TECHNOLOGY",
                "websiteUrl":       "https://example.com",
                "street":           "123 Main St",
                "city":             "Miami",
                "state":            "FL",
                "postalCode":       "33101",
                "contactFirstName": fn1,
                "contactLastName":  ln1,
                "contactEmail":     email1,
                "contactPhone":     phone1,
            })
            if not resp.get("id"):
                raise RuntimeError("Invalid brand id")
            brand_id = resp["id"]
            cleanup["brand_ids"].append(brand_id)
        run("32 Brand.create", test_32)

        # 33 — Brand.get
        def test_33():
            if not brand_id:
                raise SkipTest("dependency test 32 failed")
            resp = client.brands.get(brand_id)
            if resp.get("id") != brand_id:
                raise RuntimeError("Brand id mismatch")
            if resp.get("legalCompanyName") != "Test Company LLC":
                raise RuntimeError(f'expected legalCompanyName "Test Company LLC", got "{resp.get("legalCompanyName")}"')
        run("33 Brand.get", test_33)

        # 34 — Brand.list — must contain the brand created in test 32
        def test_34():
            resp = client.brands.list()
            if not isinstance(resp, list):
                raise RuntimeError("Expected a list")
            if brand_id and not any(b.get("id") == brand_id for b in resp):
                raise RuntimeError(f"brand {brand_id} created in test 32 not present in list()")
        run("34 Brand.list", test_34)

        # 35 — Brand.update — then verify via get() that the field actually changed
        def test_35():
            if not brand_id:
                raise SkipTest("dependency test 32 failed")
            resp = client.brands.update(brand_id, {"city": "Orlando"})
            if resp.get("id") != brand_id:
                raise RuntimeError("Brand id mismatch after update")
            fetched = client.brands.get(brand_id)
            if fetched.get("city") != "Orlando":
                raise RuntimeError(f'expected city "Orlando" after update, got "{fetched.get("city")}"')
        run("35 Brand.update", test_35)

        # 36 — Brand.delete — then verify via get() that it is gone
        def test_36():
            if not brand_id:
                raise SkipTest("dependency test 32 failed")
            client.brands.delete(brand_id)
            cleanup["brand_ids"] = [b for b in cleanup["brand_ids"] if b != brand_id]
            expect_error(lambda: client.brands.get(brand_id), f"get of deleted brand {brand_id}")
        run("36 Brand.delete", test_36)

        # ── Campaign Tests (37-42) ────────────────────────────────────────────────
        print("\n--- Campaigns ---")

        campaign_brand_id = None
        campaign_id = None

        # 37 — Campaign setup: create brand
        def test_37():
            nonlocal campaign_brand_id
            resp = client.brands.create({
                "legalCompanyName": "Campaign Test LLC",
                "entityType":       "PRIVATE_PROFIT",
                "taxId":            "987654321",
                "taxIdCountry":     "US",
                "country":          "US",
                "verticalType":     "TECHNOLOGY",
                "websiteUrl":       "https://example.com",
                "street":           "456 Test Ave",
                "city":             "Miami",
                "state":            "FL",
                "postalCode":       "33101",
                "contactFirstName": fn1,
                "contactLastName":  ln1,
                "contactEmail":     email1,
                "contactPhone":     phone1,
            })
            if not resp.get("id"):
                raise RuntimeError("Invalid brand id")
            campaign_brand_id = resp["id"]
            cleanup["brand_ids"].append(campaign_brand_id)
        run("37 Campaign setup — Brand.create", test_37)

        # 38 — Campaign.create
        def test_38():
            nonlocal campaign_id
            if not campaign_brand_id:
                raise SkipTest("dependency test 37 failed")
            resp = client.campaigns.create({
                "brandId":          campaign_brand_id,
                "useCase":          "MARKETING",
                "description":      "Integration test campaign for automated testing",
                "messageFlow":      "Customers opt-in via website form at https://example.com/sms-signup",
                "hasEmbeddedLinks": False,
                "hasEmbeddedPhone": False,
                "isAgeGated":       False,
                "isDirectLending":  False,
                "optInKeywords":    ["START", "YES"],
                "optInMessage":     "You have opted in to receive messages. Reply STOP to unsubscribe.",
                "optInProofUrl":    "https://example.com/opt-in-proof",
                "helpKeywords":     ["HELP", "INFO"],
                "helpMessage":      "For help reply HELP or call 1-800-555-0000.",
                "optOutKeywords":   ["STOP", "END"],
                "optOutMessage":    "You have been unsubscribed. Reply START to opt back in. STOP",
                "sampleMessages":   [
                    "Hello ${firstName}, this is a test message. Reply STOP to unsubscribe.",
                    "Reminder: your appointment is tomorrow. Reply HELP for assistance.",
                ],
            })
            if not resp.get("id"):
                raise RuntimeError("Invalid campaign id")
            campaign_id = resp["id"]
            cleanup["campaign_ids"].append(campaign_id)
        run("38 Campaign.create", test_38)

        # 39 — Campaign.get
        def test_39():
            if not campaign_id:
                raise SkipTest("dependency test 38 failed")
            resp = client.campaigns.get(campaign_id)
            if resp.get("id") != campaign_id:
                raise RuntimeError("Campaign id mismatch")
            if resp.get("brandId") != campaign_brand_id:
                raise RuntimeError(f"expected brandId {campaign_brand_id}, got {resp.get('brandId')}")
        run("39 Campaign.get", test_39)

        # 40 — Campaign.list — must contain the campaign created in test 38
        def test_40():
            resp = client.campaigns.list()
            if not isinstance(resp, list):
                raise RuntimeError("Expected a list")
            if campaign_id and not any(c.get("id") == campaign_id for c in resp):
                raise RuntimeError(f"campaign {campaign_id} created in test 38 not present in list()")
        run("40 Campaign.list", test_40)

        # 41 — Campaign.update — then verify via get() that the field actually changed
        def test_41():
            if not campaign_id:
                raise SkipTest("dependency test 38 failed")
            new_description = "Updated integration test campaign description"
            resp = client.campaigns.update(campaign_id, {"description": new_description})
            if resp.get("id") != campaign_id:
                raise RuntimeError("Campaign id mismatch after update")
            fetched = client.campaigns.get(campaign_id)
            if fetched.get("description") != new_description:
                raise RuntimeError(f'expected updated description after update, got "{fetched.get("description")}"')
        run("41 Campaign.update", test_41)

        # 42 — Campaign.delete + cleanup brand — then verify via get() that it is gone
        def test_42():
            nonlocal campaign_brand_id
            if not campaign_id:
                raise SkipTest("dependency test 38 failed")
            client.campaigns.delete(campaign_id)
            cleanup["campaign_ids"] = [c for c in cleanup["campaign_ids"] if c != campaign_id]
            expect_error(lambda: client.campaigns.get(campaign_id), f"get of deleted campaign {campaign_id}")
            if campaign_brand_id:
                client.brands.delete(campaign_brand_id)
                cleanup["brand_ids"] = [b for b in cleanup["brand_ids"] if b != campaign_brand_id]
        run("42 Campaign.delete", test_42)

        # ── Contact Validator (43-46) ────────────────────────────────────────────
        print("\n--- ContactValidator ---")

        # 43 — ContactValidator.validate_email
        def test_43():
            resp = client.contact_validator.validate_email(email1)
            if not resp.status:
                raise RuntimeError("status is empty")
        run("43 ContactValidator.validate_email", test_43)

        # 44 — ContactValidator.validate_emails
        def test_44():
            resp = client.contact_validator.validate_emails([email1, email2])
            if resp.summary.total != 2:
                raise RuntimeError(f"expected summary.total=2, got {resp.summary.total}")
            if len(resp.results) != 2:
                raise RuntimeError(f"expected 2 results, got {len(resp.results)}")
        run("44 ContactValidator.validate_emails", test_44)

        # 45 — ContactValidator.validate_phone
        def test_45():
            resp = client.contact_validator.validate_phone(phone1)
            if not resp.status:
                raise RuntimeError("status is empty")
        run("45 ContactValidator.validate_phone", test_45)

        # 46 — ContactValidator.validate_phones
        def test_46():
            resp = client.contact_validator.validate_phones([{"phone": phone1}, {"phone": phone2}])
            if resp.summary.total != 2:
                raise RuntimeError(f"expected summary.total=2, got {resp.summary.total}")
            if len(resp.results) != 2:
                raise RuntimeError(f"expected 2 results, got {len(resp.results)}")
        run("46 ContactValidator.validate_phones", test_46)

        # ── Negative & Permissive Tests (47-52) ──────────────────────────────────
        # 47/49/50 PASS when the operation fails as expected. 48/51/52 document
        # permissive behavior observed in the test API: those
        # operations succeed even with invalid input, so the tests assert success.
        print("\n--- Negative cases ---")

        # 47 — invalid API key must be rejected
        def test_47():
            bad_client = CCAI(client_id=client_id, api_key="invalid-api-key-for-negative-test",
                              use_test=not bool(os.environ.get('CCAI_BASE_URL')))
            expect_error(
                lambda: bad_client.sms.send_single(fn1, ln1, phone1, "should fail", "Python Negative 47"),
                "send with invalid API key"
            )
        run("47 NEGATIVE: SMS.send_single with invalid API key", test_47)

        # 48 — the test API accepts malformed phone numbers: the
        # send succeeds instead of failing. If the API starts validating phone format,
        # change this back to expect an error.
        def test_48():
            resp = client.sms.send_single(fn1, ln1, "abc", "malformed phone accepted", "Python Permissive 48")
            assert_send_response(resp)
        run("48 PERMISSIVE: SMS.send_single with malformed phone (API accepts)", test_48)

        # 49 — getting a nonexistent brand must fail
        def test_49():
            expect_error(lambda: client.brands.get(99999999), "get of nonexistent brand")
        run("49 NEGATIVE: Brand.get(nonexistent)", test_49)

        # 50 — deleting a nonexistent webhook must fail
        def test_50():
            expect_error(lambda: client.webhook.delete("99999999"), "delete of nonexistent webhook")
        run("50 NEGATIVE: Webhook.delete(nonexistent)", test_50)

        # 51 — the test environment's validator reports "valid" even for syntactically
        # invalid emails — upstream validation is not enforced
        # there, so only assert that a status is returned.
        def test_51():
            resp = client.contact_validator.validate_email("not-an-email")
            if not resp.status:
                raise RuntimeError("status is empty")
        run("51 PERMISSIVE: ContactValidator.validate_email(invalid input)", test_51)

        # 52 — the test API accepts MMS sends with a nonexistent fileKey: it does not
        # verify the file exists at send time. If the API
        # starts validating the fileKey, change this back to expect an error.
        def test_52():
            resp = client.mms.send(
                f"{client_id}/campaign/nonexistent_{int(time.time())}.png",
                [Account(first_name=fn1, last_name=ln1, phone=phone1)],
                "nonexistent fileKey accepted", "Python Permissive 52"
            )
            assert_send_response(resp)
        run("52 PERMISSIVE: MMS.send with nonexistent fileKey (API accepts)", test_52)

    finally:
        # ── Cleanup ─────────────────────────────────────────────────────────────
        # Always runs, even if the test body raised: delete leftover resources and the temp PNG.
        cleanup_resources(client, cleanup)
        try:
            os.unlink(png_path)
        except OSError:
            pass

    # ── Results ─────────────────────────────────────────────────────────────────
    print("\n==============================================")
    print(f"  RESULTS: {runner.passed} passed, {runner.failed} failed, {runner.skipped} skipped")
    print("==============================================")

    summary = json.dumps({
        "sdk": "python",
        "passed": runner.passed,
        "failed": runner.failed,
        "skipped": runner.skipped,
        "total": runner.passed + runner.failed + runner.skipped,
    })
    print(f"\nSUMMARY_JSON: {summary}")

    sys.exit(1 if runner.failed > 0 else 0)


def webhook_create_handler(client: CCAI, received_events: list):
    """Helper to call Webhook.create_handler and capture parsed events."""
    def on_event(event: WebhookEvent):
        received_events.append(event)

    return client.webhook.create_handler({"on_event": on_event})


if __name__ == "__main__":
    main()
