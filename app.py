from flask import Flask, render_template, request, session, Response
import os
import smtplib
import datetime
from email.message import EmailMessage

# ==================================================
# APP CONFIG
# ==================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wildlight-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

# ==================================================
# SMTP CONFIG (GMAIL SMTP AUTH + APP PASSWORD)
# ==================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.environ.get("SMTP_USER", "contact@wildlightstudiocr.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

EMAIL_FROM = SMTP_USER
EMAIL_TO = [
    "licensing@wildlightstudiocr.com",
    "contact@wildlightstudiocr.com"
]

# ==================================================
# TEXTOS INTERNACIONALIZADOS
# ==================================================
TEXTS = {
    "en": {
        "home_title": "Wildlight Studio",
        "home_subtitle": "Wildlife & nature photography",
        "cta_galleries": "Explore Galleries",
        "about_title": "About Wildlight Studio",
        "about_p1": "Wildlight Studio is a personal photography project dedicated to wildlife.",
        "about_p2": "The work focuses especially on birds and their natural habitats.",
        "about_p3": "Photography is about patience, respect, and light.",
        "licensing_title": "Licensing & Usage",
        "licensing_p1": "All photographs are protected by copyright.",
        "licensing_p2": "Images are available for editorial and commercial use.",
        "licensing_p3": "Contact me for licensing details.",
        "licensing_cta": "Contact for Licensing",
        "contact_title": "Contact",
        "contact_intro": "Interested in licensing an image or purchasing a print?",
        "contact_success": "Thank you for your message. I’ll contact you shortly.",
        "send_request": "Send Request"
    },
    "es": {
        "home_title": "Wildlight Studio",
        "home_subtitle": "Fotografía de naturaleza y vida silvestre",
        "cta_galleries": "Explorar Galerías",
        "about_title": "Sobre Wildlight Studio",
        "about_p1": "Wildlight Studio es un proyecto personal dedicado a la fotografía de vida silvestre.",
        "about_p2": "El trabajo se enfoca especialmente en aves y sus hábitats naturales.",
        "about_p3": "La fotografía trata sobre paciencia, respeto y luz.",
        "licensing_title": "Licencias y Uso",
        "licensing_p1": "Todas las fotografías están protegidas por derechos de autor.",
        "licensing_p2": "Las imágenes están disponibles para uso editorial y comercial.",
        "licensing_p3": "Contáctame para detalles de licencias.",
        "licensing_cta": "Contacto para licencias",
        "contact_title": "Contacto",
        "contact_intro": "¿Interesado en licenciar una imagen o comprar una impresión?",
        "contact_success": "Gracias por tu mensaje. Me pondré en contacto contigo pronto.",
        "send_request": "Enviar solicitud"
    }
}

# ==================================================
# UTILIDADES
# ==================================================
def get_lang():
    if "lang" in request.args and request.args["lang"] in TEXTS:
        session["lang"] = request.args["lang"]
    return session.get("lang", "en")


def render_page(template, **kwargs):
    lang = get_lang()
    context = {
        "texts": TEXTS[lang],
        "lang": lang
    }
    context.update(kwargs)
    return render_template(template, **context)


def get_related_photos(category, current_photo, limit=4):
    folder = os.path.join(IMAGES_DIR, category)
    if not os.path.exists(folder):
        return []

    photos = [
        f.replace(".jpg", "")
        for f in sorted(os.listdir(folder))
        if f.lower().endswith(".jpg") and f != f"{current_photo}.jpg"
    ]
    return photos[:limit]

# ==================================================
# EMAIL
# ==================================================
def send_email(name, email, message, photo=None):
    if not SMTP_PASSWORD:
        print("❌ SMTP_PASSWORD no configurado")
        return

    # Sanitizar photo para evitar headers inválidos
    photo_clean = photo.strip().replace("\n", "").replace("\r", "") if photo else ""
    photo_label = photo_clean if photo_clean else "General inquiry"

    subject = f"License request – {photo_label} | Wildlight Studio"

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(EMAIL_TO)
        msg["Reply-To"] = email

        msg.set_content(
            f"""New contact request from Wildlight Studio

Name: {name}
Email: {email}
Photo of interest: {photo_label}

Message:
{message}
"""
        )

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent | {subject}")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ==================================================
# RUTAS
# ==================================================
@app.route("/")
def home():
    return render_page("index.html")


@app.route("/galleries")
def galleries():
    categories = []
    preview_images = {}

    if os.path.exists(IMAGES_DIR):
        for category in sorted(os.listdir(IMAGES_DIR)):
            path = os.path.join(IMAGES_DIR, category)
            if os.path.isdir(path):
                images = [i for i in os.listdir(path) if i.lower().endswith(".jpg")]
                if images:
                    categories.append(category)
                    preview_images[category] = sorted(images)[0]

    return render_page(
        "galleries.html",
        categories=categories,
        preview_images=preview_images
    )


@app.route("/gallery/<category>")
def gallery(category):
    folder = os.path.join(IMAGES_DIR, category)
    photos = []

    if os.path.exists(folder):
        photos = [
            f.replace(".jpg", "")
            for f in sorted(os.listdir(folder))
            if f.lower().endswith(".jpg")
        ]

    return render_page("gallery.html", category=category, photos=photos)


@app.route("/photo/<category>/<photo_id>")
def photo(category, photo_id):
    return render_page(
        "photo.html",
        category=category,
        photo_id=photo_id,
        related_photos=get_related_photos(category, photo_id)
    )


@app.route("/about")
def about():
    return render_page("about.html")


@app.route("/licensing")
def licensing():
    return render_page("licensing.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    photo = (
        request.form.get("photo_id")
        or request.form.get("photo")
        or request.args.get("photo")
        or ""
    )

    if request.method == "POST":
        email = request.form.get("email")
        message = request.form.get("message")
        name = request.form.get("name", "N/A")

        if not email or not message:
            return render_page("contact.html", error=True, photo=photo)

        send_email(name, email, message, photo)

        return render_page("contact.html", success=True, photo=photo)

    return render_page("contact.html", photo=photo)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
