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
# TEXTS (I18N)
# ==================================================
TEXTS = {
    "en": {
        "home_title": "Wildlight Studio",
        "home_subtitle": "Wildlife & nature photography",
        "cta_galleries": "Explore Galleries",
        "send_request": "Send Request"
    },
    "es": {
        "home_title": "Wildlight Studio",
        "home_subtitle": "Fotografía de naturaleza y vida silvestre",
        "cta_galleries": "Explorar Galerías",
        "send_request": "Enviar solicitud"
    }
}

# ==================================================
# UTILITIES
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
    return sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".webp"))
    )


def get_related_photos(category, current_photo, limit=4):
    folder = os.path.join(IMAGES_DIR, category, "thumbnails")
    photos = list_photos(folder)
    return [p for p in photos if p != current_photo][:limit]

# ==================================================
# ROUTES
# ==================================================
@app.route("/")
def home():
    return render_page("index.html")


@app.route("/galleries")
def galleries():
    # USAMOS ARCHIVOS QUE SÍ EXISTEN
    preview_images = {
        "birds": "keel-billed-toucan.jpg",
        "landscapes": "sun-set-cr.jpg",
        "snakes": "eyelash-viper-1.jpg"
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

        if SMTP_PASSWORD:
            msg = EmailMessage()
            msg["Subject"] = f"License request – {photo or 'General inquiry'}"
            msg["From"] = EMAIL_FROM
            msg["To"] = ", ".join(EMAIL_TO)
            msg["Reply-To"] = email
            msg.set_content(message)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

        return render_page("contact.html", success=True, photo=photo)

    return render_page("contact.html", photo=photo)

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
