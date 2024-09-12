import requests
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

class MailgunAPIBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of emails successfully sent.
        """
        if not email_messages:
            return 0

        sent_count = 0

        for message in email_messages:
            response = self._send_email_via_mailgun(message)
            if response and response.status_code == 200:
                sent_count += 1
            else:
                logger.error(f"Failed to send email to {message.to}. Status code: {response.status_code if response else 'No Response'}")

        return sent_count

    def _send_email_via_mailgun(self, message: EmailMessage):
        """
        Helper method to send an individual email message using the Mailgun API.
        """
        api_key = settings.MAILGUN_API_KEY
        domain = settings.MAILGUN_DOMAIN

        # Collect the email content
        data = {
            "from": message.from_email,
            "to": ','.join(message.to),
            "subject": message.subject,
            "text": message.body  # Plain text version
        }

        # Add the HTML content if available
        html_content = next((content for content, mimetype in getattr(message, 'alternatives', []) if mimetype == 'text/html'), None)
        if html_content:
            data['html'] = html_content
        else:
            logger.error("No HTML content found for email.")

        # Log the outgoing data (without sensitive info like API keys)
        logger.info(f"Sending email to Mailgun with subject: {message.subject}, recipients: {message.to}")

        try:
            # Send the email via Mailgun API
            response = requests.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=("api", api_key),
                data=data
            )

            # Log response success or error
            if response.status_code != 200:
                logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while sending email via Mailgun: {e}")
            return None
