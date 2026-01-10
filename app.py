from flask import Flask, render_template, request, session
import os
import smtplib
from email.message import EmailMessage

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wildlight-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

SMTP_SERVER = "smtp-relay.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "contact@wildlightstudiocr.com"
EMAIL_TO = "licensing@wildlightstudiocr.com"


# =========================
# TEXTOS INTERNACIONALIZADOS
# =========================
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


# =========================
# UTILIDADES
# =========================
def get_lang():
    """Detecta idioma desde URL o sesión"""
    if "lang" in request.args and request.args["lang"] in TEXTS:
        session["lang"] = request.args["lang"]
    return session.get("lang", "en")


def render_page(template, **kwargs):
    """Render centralizado (menos repetición, más limpio)"""
    lang = get_lang()
    context = {
        "texts": TEXTS[lang],
        "lang": lang
    }
    context.update(kwargs)
    return render_template(template, **context)


def get_related_photos(category, current_photo, limit=4):
    """Obtiene fotos relacionadas eficientemente"""
    folder = os.path.join(IMAGES_DIR, category)
    if not os.path.exists(folder):
        return []

    photos = [
        f.replace(".jpg", "")
        for f in os.listdir(folder)
        if f.endswith(".jpg") and f != f"{current_photo}.jpg"
    ]
    return photos[:limit]


def send_email(name, email, message, photo=None):
    """Envía correo usando Gmail SMTP Relay"""
    msg = EmailMessage()
    msg["Subject"] = "New contact request | Wildlight Studio"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Reply-To"] = email

    msg.set_content(
        f"""
New contact request from Wildlight Studio

Name: {name}
Email: {email}
Photo: {photo or "N/A"}

Message:
{message}
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.send_message(msg)


# =========================
# RUTAS
# =========================
@app.route("/", strict_slashes=False)
def home():
    return render_page(
        "index.html",
        meta_description="Wildlife and nature photography by Wildlight Studio. Licensing and fine art prints available."
    )


@app.route("/galleries", strict_slashes=False)
def galleries():
    return render_page(
        "galleries.html",
        meta_description="Wildlife photography galleries by Wildlight Studio. Explore birds and nature collections."
    )


@app.route("/about", strict_slashes=False)
def about():
    return render_page(
        "about.html",
        meta_description="About Wildlight Studio, a wildlife and nature photography project focused on birds."
    )


@app.route("/licensing", strict_slashes=False)
def licensing():
    return render_page(
        "licensing.html",
        meta_description="Wildlife photography licensing and usage information. Editorial and commercial licenses available."
    )


@app.route("/contact", methods=["GET", "POST"], strict_slashes=False)
def contact():
    photo = request.args.get("photo")

    if request.method == "POST":
        send_email(
            name=request.form.get("name"),
            email=request.form.get("email"),
            message=request.form.get("message"),
            photo=request.form.get("photo_id")
        )

        return render_page(
            "contact.html",
            success=True,
            photo=request.form.get("photo_id"),
            meta_description="Contact Wildlight Studio for wildlife photography licensing, fine art prints, or collaborations."
        )

    return render_page(
        "contact.html",
        photo=photo,
        meta_description="Contact Wildlight Studio for wildlife photography licensing, fine art prints, or collaborations."
    )


@app.route("/gallery/<category>", strict_slashes=False)
def gallery(category):
    return render_page(
        "gallery.html",
        category=category,
        meta_description=f"{category.capitalize()} wildlife photography gallery by Wildlight Studio."
    )


@app.route("/photo/<category>/<photo_id>", strict_slashes=False)
def photo(category, photo_id):
    related_photos = get_related_photos(category, photo_id)

    return render_page(
        "photo.html",
        category=category,
        photo_id=photo_id,
        related_photos=related_photos,
        meta_description=f"{category.capitalize()} wildlife photograph available for licensing and fine art prints by Wildlight Studio."
    )


# =========================
# ARRANQUE LOCAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
