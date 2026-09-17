import os
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def forge_corporate_email(
    subject, html_body, text_body, to, extra_images=None, **kwargs
):
    # related = MIMEMultipart("related")
    if extra_images is None:
        extra_images = {}
    html_content = render_to_string(
        "email/email.html",
        {
            "body": html_body,
            "subject": subject,
            "corp_color": "#502c1d",
            "BASE_URL": settings.BASE_URL,
        },
    )
    text_content = strip_tags(
        render_to_string(
            "email/email_text.html",
            {
                "body": text_body,
                "subject": subject,
                "corp_color": "#502c1d",
                "BASE_URL": settings.BASE_URL,
            },
        )
    )

    if "from_email" in kwargs:
        from_email = kwargs.pop("from_email")
    else:
        from_email = settings.DEFAULT_FROM_EMAIL

    email = EmailMultiAlternatives(
        subject=subject, body=text_content, from_email=from_email, to=to, **kwargs
    )

    email.attach_alternative(html_content, "text/html")

    with open(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "images", "email-logo.png"
        ),
        "rb",
    ).read() as img:
        logo_image = MIMEImage(img)
        logo_image.add_header("Content-ID", "<email-logo.png>")
        logo_image.add_header(
            "Content-Disposition", "inline", filename="email-logo.png"
        )
        logo_image.add_header("Content-Type", "image/png", name="email-logo.png")
        email.attach(logo_image)

    for img_id, img_path in extra_images.items():
        try:
            with open(img_path, "rb").read() as img:
                logo_image = MIMEImage(img)
                logo_image.add_header("Content-ID", f"<{img_id}>")
                logo_image.add_header("Content-Disposition", "inline", filename=img_id)
                subtype = "jpeg"
                if img_path.lower().endswith("png"):
                    subtype = "png"
                logo_image.add_header("Content-Type", f"image/{subtype}", name=img_id)
                email.attach(logo_image)
        except Exception:  # noqa: BLE001, S110
            pass

    email.mixed_subtype = "related"
    return email


def send_email(
    subject, html_body, text_body, to, extra_images=None, do_send=True, **kwargs
):
    if extra_images is None:
        extra_images = {}
    email = forge_corporate_email(
        subject, html_body, text_body, to, extra_images={}, **kwargs
    )

    if do_send:
        return email.send()
    else:
        return email
