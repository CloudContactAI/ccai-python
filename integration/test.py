"""
Python SDK integration tests — 42 tests
Covers: SMS (1-6), MMS (7-17), Email (18-22), Webhook (23-29), Contact (30-31), Brands (32-36), Campaigns (37-42)
"""

import base64
import hmac
import hashlib
import json
import os
import sys
import tempfile

# The SDK is installed in the Docker container via pip install -e /sdk
from ccai_python.ccai import CCAI
from ccai_python.sms.sms import Account
from ccai_python.email_service import EmailAccount, EmailCampaign
from ccai_python.webhook import WebhookConfig, WebhookEvent, WebhookEventType

# ── Helpers ───────────────────────────────────────────────────────────────────

passed = 0
failed = 0


def run(name: str, fn) -> None:
    global passed, failed
    try:
        fn()
        print(f"  PASS [{name}]")
        passed += 1
    except Exception as e:
        print(f"  FAIL [{name}]: {e}")
        failed += 1


def must_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        print(f"ERROR: required env var {key} is not set")
        sys.exit(2)
    return val


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


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    global passed, failed

    # Validate required env vars
    client_id  = must_env("CCAI_CLIENT_ID")
    api_key    = must_env("CCAI_API_KEY")
    phone1     = must_env("CCAI_TEST_PHONE")
    phone2     = must_env("CCAI_TEST_PHONE_2")
    phone3     = must_env("CCAI_TEST_PHONE_3")
    email1     = must_env("CCAI_TEST_EMAIL")
    email2     = must_env("CCAI_TEST_EMAIL_2")
    email3     = must_env("CCAI_TEST_EMAIL_3")
    fn1        = must_env("CCAI_TEST_FIRST_NAME")
    ln1        = must_env("CCAI_TEST_LAST_NAME")
    fn2        = must_env("CCAI_TEST_FIRST_NAME_2")
    ln2        = must_env("CCAI_TEST_LAST_NAME_2")
    fn3        = must_env("CCAI_TEST_FIRST_NAME_3")
    ln3        = must_env("CCAI_TEST_LAST_NAME_3")
    webhook_url = must_env("WEBHOOK_URL")

    # Use CCAI_BASE_URL if set (local dev), otherwise fall back to test environment
    client = CCAI(client_id=client_id, api_key=api_key,
                  use_test=not bool(os.environ.get('CCAI_BASE_URL')))

    print("==============================================")
    print("  CCAI Python SDK Integration Tests")
    print("==============================================")

    # Write temp PNG for MMS tests
    png_path = write_temp_png()

    # ── SMS Tests (1-6) ──────────────────────────────────────────────────────────
    print("\n--- SMS ---")

    # 01 — SMS.send_single
    def test_01():
        client.sms.send_single(fn1, ln1, phone1, "Hello from Python SDK!", "Python Test")
    run("01 SMS.send_single", test_01)

    # 02 — SMS.send (1 recipient)
    def test_02():
        client.sms.send(
            [Account(first_name=fn1, last_name=ln1, phone=phone1)],
            "Hello 1 recipient!", "Python Test"
        )
    run("02 SMS.send (1 recipient)", test_02)

    # 03 — SMS.send (2 recipients)
    def test_03():
        client.sms.send(
            [
                Account(first_name=fn1, last_name=ln1, phone=phone1),
                Account(first_name=fn2, last_name=ln2, phone=phone2),
            ],
            "Hello 2 recipients!", "Python Test"
        )
    run("03 SMS.send (2 recipients)", test_03)

    # 04 — SMS.send (3 recipients)
    def test_04():
        client.sms.send(
            [
                Account(first_name=fn1, last_name=ln1, phone=phone1),
                Account(first_name=fn2, last_name=ln2, phone=phone2),
                Account(first_name=fn3, last_name=ln3, phone=phone3),
            ],
            "Hello 3 recipients!", "Python Test"
        )
    run("04 SMS.send (3 recipients)", test_04)

    # 05 — SMS.send with data
    def test_05():
        client.sms.send(
            [Account(first_name=fn1, last_name=ln1, phone=phone1, data={"city": "Miami", "offer": "20% off"})],
            "Hello from ${city}! Claim your ${offer}.", "Python Test Data"
        )
    run("05 SMS.send with data", test_05)

    # 06 — SMS.send with message_data
    def test_06():
        client.sms.send(
            [Account(first_name=fn1, last_name=ln1, phone=phone1, message_data='{"trackingId":"abc123"}')],
            "Hello with messageData!", "Python Test MsgData"
        )
    run("06 SMS.send with message_data", test_06)

    # ── MMS Tests (7-17) ─────────────────────────────────────────────────────────
    print("\n--- MMS ---")

    signed_url_resp = None
    mms_dep_failed = False

    # 07 — MMS.get_signed_upload_url
    def test_07():
        nonlocal signed_url_resp, mms_dep_failed
        resp = client.mms.get_signed_upload_url("test_image.png", "image/png")
        if not resp.get("signedS3Url"):
            mms_dep_failed = True
            raise RuntimeError("signedS3Url is empty")
        signed_url_resp = resp
    run("07 MMS.get_signed_upload_url", test_07)

    # 08 — MMS.upload_image_to_signed_url
    def test_08():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        ok = client.mms.upload_image_to_signed_url(signed_url_resp["signedS3Url"], png_path, "image/png")
        if not ok:
            raise RuntimeError("upload returned False")
    run("08 MMS.upload_image_to_signed_url", test_08)

    # 09 — MMS.send_single
    def test_09():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send_single(signed_url_resp["fileKey"], fn1, ln1, phone1, "MMS single!", "Python MMS Test")
    run("09 MMS.send_single", test_09)

    # 10 — MMS.send (1 recipient)
    def test_10():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send(
            signed_url_resp["fileKey"],
            [Account(first_name=fn1, last_name=ln1, phone=phone1)],
            "MMS 1 recipient!", "Python MMS Test"
        )
    run("10 MMS.send (1 recipient)", test_10)

    # 11 — MMS.send (2 recipients)
    def test_11():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send(
            signed_url_resp["fileKey"],
            [
                Account(first_name=fn1, last_name=ln1, phone=phone1),
                Account(first_name=fn2, last_name=ln2, phone=phone2),
            ],
            "MMS 2 recipients!", "Python MMS Test"
        )
    run("11 MMS.send (2 recipients)", test_11)

    # 12 — MMS.send (3 recipients)
    def test_12():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send(
            signed_url_resp["fileKey"],
            [
                Account(first_name=fn1, last_name=ln1, phone=phone1),
                Account(first_name=fn2, last_name=ln2, phone=phone2),
                Account(first_name=fn3, last_name=ln3, phone=phone3),
            ],
            "MMS 3 recipients!", "Python MMS Test"
        )
    run("12 MMS.send (3 recipients)", test_12)

    # 13 — MMS.send with data
    def test_13():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send(
            signed_url_resp["fileKey"],
            [Account(first_name=fn1, last_name=ln1, phone=phone1, data={"product": "Widget"})],
            "Check out ${product}!", "Python MMS Data"
        )
    run("13 MMS.send with data", test_13)

    # 14 — MMS.send with message_data
    def test_14():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send(
            signed_url_resp["fileKey"],
            [Account(first_name=fn1, last_name=ln1, phone=phone1, message_data='{"campaignId":"mms-py-001"}')],
            "MMS with messageData!", "Python MMS MsgData"
        )
    run("14 MMS.send with message_data", test_14)

    # 15 — MMS.check_file_uploaded
    def test_15():
        if mms_dep_failed or not signed_url_resp:
            raise RuntimeError("dependency test 07 failed")
        client.mms.check_file_uploaded(signed_url_resp["fileKey"])
    run("15 MMS.check_file_uploaded", test_15)

    # 16 — MMS.send_with_image (fresh upload)
    def test_16():
        if mms_dep_failed:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send_with_image(
            png_path, "image/png",
            [Account(first_name=fn1, last_name=ln1, phone=phone1)],
            "MMS with image!", "Python MMS Image",
            force_new_campaign=True
        )
    run("16 MMS.send_with_image (fresh upload)", test_16)

    # 17 — MMS.send_with_image (cached)
    def test_17():
        if mms_dep_failed:
            raise RuntimeError("dependency test 07 failed")
        client.mms.send_with_image(
            png_path, "image/png",
            [Account(first_name=fn1, last_name=ln1, phone=phone1)],
            "MMS cached image!", "Python MMS Cache",
            force_new_campaign=True
        )
    run("17 MMS.send_with_image (cached)", test_17)

    # ── Email Tests (18-22) ──────────────────────────────────────────────────────
    print("\n--- Email ---")

    SENDER_EMAIL = "noreply@cloudcontactai.com"
    SENDER_NAME  = "CCAI Test"
    REPLY_EMAIL  = "noreply@cloudcontactai.com"

    # 18 — Email.send_single
    def test_18():
        client.email.send_single(
            fn1, ln1, email1,
            "Python SDK Test Email",
            "<p>Hello from Python SDK!</p>",
            sender_email=SENDER_EMAIL,
            reply_email=REPLY_EMAIL,
            sender_name=SENDER_NAME,
            title="Python Email Test"
        )
    run("18 Email.send_single", test_18)

    # 19 — Email.send (1 recipient)
    def test_19():
        client.email.send(
            [EmailAccount(first_name=fn1, last_name=ln1, email=email1)],
            "Python SDK Email 1", "<p>Hello 1!</p>",
            SENDER_EMAIL, REPLY_EMAIL, SENDER_NAME, "Python Email Test"
        )
    run("19 Email.send (1 recipient)", test_19)

    # 20 — Email.send (2 recipients)
    def test_20():
        client.email.send(
            [
                EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                EmailAccount(first_name=fn2, last_name=ln2, email=email2),
            ],
            "Python SDK Email 2", "<p>Hello 2!</p>",
            SENDER_EMAIL, REPLY_EMAIL, SENDER_NAME, "Python Email Test"
        )
    run("20 Email.send (2 recipients)", test_20)

    # 21 — Email.send (3 recipients)
    def test_21():
        client.email.send(
            [
                EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                EmailAccount(first_name=fn2, last_name=ln2, email=email2),
                EmailAccount(first_name=fn3, last_name=ln3, email=email3),
            ],
            "Python SDK Email 3", "<p>Hello 3!</p>",
            SENDER_EMAIL, REPLY_EMAIL, SENDER_NAME, "Python Email Test"
        )
    run("21 Email.send (3 recipients)", test_21)

    # 22 — Email.send_campaign (direct campaign object)
    def test_22():
        campaign = EmailCampaign(
            subject="Python SDK Campaign Test",
            title="Python Email Campaign",
            message="<p>Campaign email from Python SDK!</p>",
            sender_email=SENDER_EMAIL,
            reply_email=REPLY_EMAIL,
            sender_name=SENDER_NAME,
            accounts=[
                EmailAccount(first_name=fn1, last_name=ln1, email=email1),
                EmailAccount(first_name=fn2, last_name=ln2, email=email2),
            ],
        )
        client.email.send_campaign(campaign)
    run("22 Email.send_campaign", test_22)

    # ── Webhook Tests (23-29) ────────────────────────────────────────────────────
    print("\n--- Webhook ---")

    SECRET = "test-webhook-secret-python"
    registered_webhook_id = None

    # 23 — Webhook.register
    def test_23():
        nonlocal registered_webhook_id
        config = WebhookConfig(
            url=webhook_url,
            events=[WebhookEventType.MESSAGE_SENT],
            secret=SECRET
        )
        resp = client.webhook.register(config)
        wid = resp.id
        if not wid:
            raise RuntimeError("webhook ID is empty after register")
        registered_webhook_id = str(wid)
    run("23 Webhook.register", test_23)

    # 24 — Webhook.list
    def test_24():
        hooks = client.webhook.list()
        if not isinstance(hooks, list) or len(hooks) == 0:
            raise RuntimeError("expected at least one webhook, got 0")
    run("24 Webhook.list", test_24)

    # 25 — Webhook.update
    def test_25():
        if not registered_webhook_id:
            raise RuntimeError("no webhook ID from test 23")
        client.webhook.update(
            registered_webhook_id,
            {"url": webhook_url + "?updated=1", "secret": "updated-secret-python"}
        )
    run("25 Webhook.update", test_25)

    # 26 — Webhook.verify_signature (valid)
    def test_26():
        event_hash = "abc123eventHash"
        sig = hmac_sha256_base64(SECRET, f"{client_id}:{event_hash}")
        ok = client.webhook.verify_signature(sig, client_id, event_hash, SECRET)
        if not ok:
            raise RuntimeError("expected valid signature to return True")
    run("26 Webhook.verify_signature (valid)", test_26)

    # 27 — Webhook.verify_signature (invalid)
    def test_27():
        ok = client.webhook.verify_signature("invalidsig==", client_id, "somehash", SECRET)
        if ok:
            raise RuntimeError("expected invalid signature to return False")
    run("27 Webhook.verify_signature (invalid)", test_27)

    # 28 — Webhook.create_handler (parses a webhook event)
    def test_28():
        received_events = []
        handler = Webhook_create_handler(client, received_events)
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

    # 29 — Webhook.delete
    def test_29():
        if not registered_webhook_id:
            raise RuntimeError("no webhook ID from test 23")
        client.webhook.delete(registered_webhook_id)
    run("29 Webhook.delete", test_29)

    # ── Contact Tests (30-31) ────────────────────────────────────────────────────
    print("\n--- Contact ---")

    # 30 — Contact.set_do_not_text(True)
    def test_30():
        client.contact.set_do_not_text(True, phone=phone1)
    run("30 Contact.set_do_not_text(True)", test_30)

    # 31 — Contact.set_do_not_text(False)
    def test_31():
        client.contact.set_do_not_text(False, phone=phone1)
    run("31 Contact.set_do_not_text(False)", test_31)

    # ── Brand Tests (32-36) ──────────────────────────────────────────────────────
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
    run("32 Brand.create", test_32)

    # 33 — Brand.get
    def test_33():
        if not brand_id:
            raise RuntimeError("dependency test 32 failed")
        resp = client.brands.get(brand_id)
        if resp.get("id") != brand_id:
            raise RuntimeError("Brand id mismatch")
    run("33 Brand.get", test_33)

    # 34 — Brand.list
    def test_34():
        resp = client.brands.list()
        if not isinstance(resp, list):
            raise RuntimeError("Expected a list")
    run("34 Brand.list", test_34)

    # 35 — Brand.update
    def test_35():
        if not brand_id:
            raise RuntimeError("dependency test 32 failed")
        resp = client.brands.update(brand_id, {"city": "Orlando"})
        if resp.get("id") != brand_id:
            raise RuntimeError("Brand id mismatch after update")
    run("35 Brand.update", test_35)

    # 36 — Brand.delete
    def test_36():
        if not brand_id:
            raise RuntimeError("dependency test 32 failed")
        client.brands.delete(brand_id)
    run("36 Brand.delete", test_36)

    # ── Campaign Tests (37-42) ────────────────────────────────────────────────────
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
    run("37 Campaign setup — Brand.create", test_37)

    # 38 — Campaign.create
    def test_38():
        nonlocal campaign_id
        if not campaign_brand_id:
            raise RuntimeError("dependency test 37 failed")
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
    run("38 Campaign.create", test_38)

    # 39 — Campaign.get
    def test_39():
        if not campaign_id:
            raise RuntimeError("dependency test 38 failed")
        resp = client.campaigns.get(campaign_id)
        if resp.get("id") != campaign_id:
            raise RuntimeError("Campaign id mismatch")
    run("39 Campaign.get", test_39)

    # 40 — Campaign.list
    def test_40():
        resp = client.campaigns.list()
        if not isinstance(resp, list):
            raise RuntimeError("Expected a list")
    run("40 Campaign.list", test_40)

    # 41 — Campaign.update
    def test_41():
        if not campaign_id:
            raise RuntimeError("dependency test 38 failed")
        resp = client.campaigns.update(campaign_id, {"description": "Updated integration test campaign description"})
        if resp.get("id") != campaign_id:
            raise RuntimeError("Campaign id mismatch after update")
    run("41 Campaign.update", test_41)

    # 42 — Campaign.delete + cleanup brand
    def test_42():
        if not campaign_id:
            raise RuntimeError("dependency test 38 failed")
        client.campaigns.delete(campaign_id)
        if campaign_brand_id:
            client.brands.delete(campaign_brand_id)
    run("42 Campaign.delete", test_42)

    # ── Contact Validator ─────────────────────────────────────────────────────────

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
    run("46 ContactValidator.validate_phones", test_46)

    # ── Cleanup & Results ─────────────────────────────────────────────────────────
    os.unlink(png_path)

    print("\n==============================================")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("==============================================")

    summary = json.dumps({"sdk": "python", "passed": passed, "failed": failed, "total": passed + failed})
    print(f"\nSUMMARY_JSON: {summary}")

    sys.exit(1 if failed > 0 else 0)


def Webhook_create_handler(client: CCAI, received_events: list):
    """Helper to call Webhook.create_handler and capture parsed events."""
    def on_event(event: WebhookEvent):
        received_events.append(event)

    return client.webhook.create_handler({"on_event": on_event})


if __name__ == "__main__":
    main()
