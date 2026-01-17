from flask import Flask, render_template, request, session, abort
import os
import smtplib
from email.message import EmailMessage

# ==================================================
# APP CONFIG
# ==================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wildlight-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "assets", "img")

# Categorías disponibles
CATEGORIES = ["birds", "landscapes", "snakes"]

# ==================================================
# SMTP CONFIG
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
    lang = request.args.get("lang")
    if lang in TEXTS:
        session["lang"] = lang
    return session.get("lang", "en")


def render_page(template, **kwargs):
    lang = get_lang()
    context = {
        "texts": TEXTS[lang],
        "lang": lang
    }
    context.update(kwargs)
    return render_template(template, **context)


def list_photos(folder):
    if not os.path.exists(folder):
        return []
    return sorted([
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".webp"))
    ])


def get_related_photos(category, current_photo, limit=4):
    folder = os.path.join(IMAGES_DIR, category, "thumbnails")
    photos = list_photos(folder)
    return [p for p in photos if p != current_photo][:limit]

# ==================================================
# EMAIL
# ==================================================
def send_email(name, email, message, photo=None):
    if not SMTP_PASSWORD:
        return

    subject = f"License request – {photo or 'General inquiry'} | Wildlight Studio"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg["Reply-To"] = email

    msg.set_content(
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Photo: {photo or 'N/A'}\n\n"
        f"{message}"
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

# ==================================================
# ROUTES
# ==================================================
@app.route("/")
def home():
    return render_page("index.html")


@app.route("/galleries")
def galleries():
    preview_images = {
        "birds": "birds-preview.webp",
        "landscapes": "landscapes-preview.webp",
        "snakes": "snakes-preview.webp"
    }

    return render_page(
        "galleries.html",
        categories=CATEGORIES,
        preview_images=preview_images
    )


@app.route("/gallery/<category>")
def gallery(category):
    if category not in CATEGORIES:
        abort(404)

    folder = os.path.join(IMAGES_DIR, category, "thumbnails")
    photos = list_photos(folder)

    return render_page(
        "gallery.html",
        category=category,
        photos=photos
    )


@app.route("/photo/<category>/<photo_id>")
def photo(category, photo_id):
    folder = os.path.join(IMAGES_DIR, category, "thumbnails")

    if photo_id not in list_photos(folder):
        abort(404)

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
    photo = request.form.get("photo") or request.args.get("photo", "")

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
