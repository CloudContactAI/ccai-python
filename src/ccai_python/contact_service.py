from typing import Optional
from pydantic import BaseModel, Field


class ContactDoNotTextRequest(BaseModel):
    client_id: str = Field(..., alias="clientId")
    contact_id: Optional[str] = Field(None, alias="contactId")
    phone: Optional[str] = None
    do_not_text: Optional[bool] = Field(None, alias="doNotText")


class ContactDoNotTextResponse(BaseModel):
    contact_id: str = Field(..., alias="contactId")
    phone: str
    do_not_text: bool = Field(..., alias="doNotText")


class Contact:
    """Contact service for managing CloudContactAI contacts"""

    def __init__(self, ccai):
        self.ccai = ccai

    def set_do_not_text(self, do_not_text: bool, contact_id: Optional[str] = None, phone: Optional[str] = None) -> ContactDoNotTextResponse:
        """Set the do-not-text status for a contact"""
        request = ContactDoNotTextRequest(
            clientId=self.ccai.client_id,
            contactId=contact_id,
            phone=phone,
            doNotText=do_not_text
        )
        response = self.ccai.request('PUT', '/account/do-not-text', request.model_dump(by_alias=True))
        return ContactDoNotTextResponse(**response)
