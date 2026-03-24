"""
Examples of using the Contact functionality in the CCAI Python library
"""

from ccai_python import CCAI

# Initialize the CCAI client
ccai = CCAI(
    client_id="<YOUR_CLIENT_ID>",
    api_key="<YOUR_API_KEY>"
)


def set_do_not_text_by_contact_id():
    """Example 1: Set do not text status using contact ID"""
    try:
        response = ccai.contact.set_do_not_text(
            do_not_text=True,
            contact_id="your-contact-id"
        )

        print(f"Contact {response.contact_id} do not text set to {response.do_not_text}")
    except Exception as error:
        print("Error marking contact as do not text by contact ID:", error)


def set_do_not_text_by_phone():
    """Example 2: Set do not text status using phone number"""
    try:
        response = ccai.contact.set_do_not_text(
            do_not_text=True,
            phone="+15551234567"
        )

        print(f"Contact {response.contact_id} ({response.phone}) do not text set to {response.do_not_text}")
    except Exception as error:
        print("Error marking contact as do not text by phone:", error)


def remove_do_not_text():
    """Example 3: Remove do not text status from a contact"""
    try:
        response = ccai.contact.set_do_not_text(
            do_not_text=False,
            contact_id="your-contact-id"
        )

        print(f"Contact {response.contact_id} do not text removed: {response.do_not_text}")
    except Exception as error:
        print("Error removing do not text:", error)


if __name__ == "__main__":
    # Run the examples
    # Uncomment the example you want to run
    set_do_not_text_by_contact_id()
    set_do_not_text_by_phone()
    remove_do_not_text()
