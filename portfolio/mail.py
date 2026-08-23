"""Email notification for new contact-form messages.

The message is saved to the database before this runs, so a mail outage can
never lose an enquiry — it just means no email that time. Nothing here raises.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

SUBJECT = "New portfolio message from {name}"

BODY = """{name} <{email}> sent this through surajportfolio.com:

{message}

--
Reply straight to this email to answer them.
Received {received} · read all messages at /admin/portfolio/contactmessage/
"""


def notify_new_message(contact_message) -> bool:
    """Email the site owner. Returns True if the message was handed to the mail backend."""
    recipient = getattr(settings, "CONTACT_NOTIFY_EMAIL", "") or ""
    if not recipient:
        logger.info("CONTACT_NOTIFY_EMAIL not set — skipping notification email.")
        return False

    try:
        email = EmailMessage(
            subject=SUBJECT.format(name=contact_message.name),
            body=BODY.format(
                name=contact_message.name,
                email=contact_message.email,
                message=contact_message.message,
                received=contact_message.received_at.strftime("%d %b %Y at %H:%M"),
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            # So hitting reply in your inbox writes back to the sender.
            reply_to=[contact_message.email],
        )
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Could not send notification for message #%s", contact_message.pk)
        return False
