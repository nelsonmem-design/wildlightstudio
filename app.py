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
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # App Password (16 dígitos)

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


def send_email(name, email, message, photo=None):
    """
    Envía el correo usando Gmail SMTP AUTH
    El asunto se genera dinámicamente según la foto de interés
    """
    if not SMTP_PASSWORD:
        print("❌ SMTP_PASSWORD no configurado")
        return

    try:
        # Asunto dinámico
        if photo:
            subject = f"License request – {photo} | Wildlight Studio"
        else:
            subject = "General inquiry | Wildlight Studio"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(EMAIL_TO)
        msg["Reply-To"] = email

        msg.set_content(f"""
New contact request from Wildlight Studio

Name: {name}
Email: {email}
Photo of interest: {photo or "N/A"}

Message:
{message}
""")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully | Subject: {subject}")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)


# ==================================================
# SITEMAP.XML
# ==================================================
@app.route("/sitemap.xml", strict_slashes=False)
def sitemap():
    base_url = "https://wildlightstudiocr.com"
    today = datetime.date.today().isoformat()
    pages = []

    static_pages = [
        ("", "1.0"),
        ("galleries", "0.9"),
        ("about", "0.7"),
        ("licensing", "0.8"),
        ("contact", "0.6"),
    ]

    for path, priority in static_pages:
        pages.append({
            "loc": f"{base_url}/{path}",
            "lastmod": today,
            "changefreq": "weekly",
            "priority": priority
        })

    if os.path.exists(IMAGES_DIR):
        for category in sorted(os.listdir(IMAGES_DIR)):
            category_path = os.path.join(IMAGES_DIR, category)
            if os.path.isdir(category_path):
                pages.append({
                    "loc": f"{base_url}/gallery/{category}",
                    "lastmod": today,
                    "changefreq": "weekly",
                    "priority": "0.9"
                })

                for img in sorted(os.listdir(category_path)):
                    if img.lower().endswith(".jpg"):
                        photo_id = img.replace(".jpg", "")
                        pages.append({
                            "loc": f"{base_url}/photo/{category}/{photo_id}",
                            "lastmod": today,
                            "changefreq": "monthly",
                            "priority": "0.7"
                        })

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for p in pages:
        xml.extend([
            "<url>",
            f"<loc>{p['loc']}</loc>",
            f"<lastmod>{p['lastmod']}</lastmod>",
            f"<changefreq>{p['changefreq']}</changefreq>",
            f"<priority>{p['priority']}</priority>",
            "</url>"
        ])

    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")

# ==================================================
# RUTAS
# ==================================================
@app.route("/")
def home():
    return render_page("index.html",
        meta_description="Wildlife and nature photography by Wildlight Studio."
    )

@app.route("/galleries")
def galleries():
    return render_page("galleries.html")

@app.route("/about")
def about():
    return render_page("about.html")

@app.route("/licensing")
def licensing():
    return render_page("licensing.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    photo = request.args.get("photo")

    if request.method == "POST":
        send_email(
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("message"),
            request.form.get("photo_id")
        )
        return render_page("contact.html", success=True, photo=photo)

    return render_page("contact.html", photo=photo)

@app.route("/gallery/<category>")
def gallery(category):
    return render_page("gallery.html", category=category)

@app.route("/photo/<category>/<photo_id>")
def photo(category, photo_id):
    return render_page(
        "photo.html",
        category=category,
        photo_id=photo_id,
        related_photos=get_related_photos(category, photo_id)
    )

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
