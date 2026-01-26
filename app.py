from flask import (
    Flask, render_template, request, session,
    abort, redirect, url_for, make_response
)
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ==================================================
# APP CONFIG
# ==================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wildlight-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "assets", "img")

CATEGORIES = ["birds", "landscapes", "snakes"]
DEFAULT_LANG = "en"
SITE_URL = "https://www.wildlightstudiocr.com"

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
# TEXTS / I18N
# ==================================================
TEXTS = {
    "en": {
        "home_title": "Wildlight Studio",
        "home_subtitle": "Wildlife & nature photography",
        "cta_galleries": "Explore Galleries",
        "cta_license": "License an Image",

        "about_title": "About Wildlight Studio",

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
        "cta_license": "Licenciar una imagen",

        "about_title": "Sobre Wildlight Studio",

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
# UTILITIES
# ==================================================
def get_lang():
    """Detecta idioma y lo normaliza."""
    lang = request.args.get("lang")

    if lang in TEXTS:
        session["lang"] = lang
    elif "lang" not in session:
        session["lang"] = DEFAULT_LANG

    return session.get("lang", DEFAULT_LANG)


def enforce_canonical():
    """
    Fuerza una única versión de URL:
    - Quita lang inválido
    - Agrega ?lang si falta
    """
    lang = request.args.get("lang")
    clean_args = dict(request.args)

    if lang not in TEXTS:
        clean_args.pop("lang", None)

    final_lang = clean_args.get("lang") or session.get("lang") or DEFAULT_LANG
    clean_args["lang"] = final_lang

    canonical_url = url_for(
        request.endpoint,
        **(request.view_args or {}),
        **clean_args
    )

    if request.full_path.rstrip("?") != canonical_url:
        return redirect(canonical_url, 301)

    return None


def render_page(template, **kwargs):
    canonical_redirect = enforce_canonical()
    if canonical_redirect:
        return canonical_redirect

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


def safe_preview_image(category, filename):
    path = os.path.join(IMAGES_DIR, category, "thumbnails", filename)
    return filename if os.path.exists(path) else None


def send_email(name, email, message, photo=None):
    if not SMTP_PASSWORD:
        print("⚠ SMTP_PASSWORD not configured")
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
    preview_images_raw = {
        "birds": "keel-billed-toucan.jpg",
        "landscapes": "sun-set-cr.jpg",
        "snakes": "eyelash-viper-1.jpg"
    }

    preview_images = {
        cat: safe_preview_image(cat, img)
        for cat, img in preview_images_raw.items()
        if safe_preview_image(cat, img)
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
    if category not in CATEGORIES:
        abort(404)

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
        name = request.form.get("name", "N/A")
        email = request.form.get("email")
        message = request.form.get("message")

        if not email or not message:
            return render_page("contact.html", error=True, photo=photo)

        send_email(name, email, message, photo)
        return render_page("contact.html", success=True, photo=photo)

    return render_page("contact.html", photo=photo)

# ==================================================
# ROBOTS.TXT
# ==================================================
@app.route("/robots.txt")
def robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    response = make_response(content)
    response.headers["Content-Type"] = "text/plain"
    return response

# ==================================================
# SITEMAP.XML
# ==================================================
@app.route("/sitemap.xml")
def sitemap():
    pages = []
    lastmod = datetime.utcnow().date().isoformat()

    def add_page(url):
        pages.append({
            "loc": f"{SITE_URL}{url}",
            "lastmod": lastmod
        })

    # Páginas principales
    for lang in TEXTS.keys():
        add_page(f"/?lang={lang}")
        add_page(f"/galleries?lang={lang}")
        add_page(f"/about?lang={lang}")
        add_page(f"/licensing?lang={lang}")
        add_page(f"/contact?lang={lang}")

    # Galerías y fotos
    for category in CATEGORIES:
        for lang in TEXTS.keys():
            add_page(f"/gallery/{category}?lang={lang}")

        folder = os.path.join(IMAGES_DIR, category, "thumbnails")
        for photo in list_photos(folder):
            for lang in TEXTS.keys():
                add_page(f"/photo/{category}/{photo}?lang={lang}")

    sitemap_xml = render_template("sitemap.xml", pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

# ==================================================
# ERROR HANDLERS
# ==================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_page("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_page("500.html"), 500

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
