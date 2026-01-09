from flask import Flask, render_template, request, session
import os

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "wildlight-secret-key"


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
# UTILIDAD IDIOMA
# =========================
def get_lang():
    if "lang" in request.args:
        lang = request.args.get("lang")
        if lang in TEXTS:
            session["lang"] = lang
            return lang

    if "lang" in session:
        return session["lang"]

    return "en"


# =========================
# HOME
# =========================
@app.route("/", strict_slashes=False)
def home():
    lang = get_lang()
    return render_template("index.html", texts=TEXTS[lang], lang=lang)


# =========================
# PÁGINAS PRINCIPALES
# =========================
@app.route("/galleries", strict_slashes=False)
def galleries():
    lang = get_lang()
    return render_template("galleries.html", texts=TEXTS[lang], lang=lang)


@app.route("/about", strict_slashes=False)
def about():
    lang = get_lang()
    return render_template("about.html", texts=TEXTS[lang], lang=lang)


@app.route("/licensing", strict_slashes=False)
def licensing():
    lang = get_lang()
    return render_template("licensing.html", texts=TEXTS[lang], lang=lang)


# =========================
# CONTACTO
# =========================
@app.route("/contact", methods=["GET", "POST"], strict_slashes=False)
def contact():
    lang = get_lang()
    photo = request.args.get("photo")

    if request.method == "POST":
        print("----- NEW REQUEST -----")
        print("Name:", request.form.get("name"))
        print("Email:", request.form.get("email"))
        print("Photo:", request.form.get("photo_id"))
        print("Message:", request.form.get("message"))
        print("-----------------------")

        return render_template(
            "contact.html",
            success=True,
            photo=request.form.get("photo_id"),
            texts=TEXTS[lang],
            lang=lang
        )

    return render_template("contact.html", photo=photo, texts=TEXTS[lang], lang=lang)


# =========================
# GALERÍA POR CATEGORÍA
# =========================
@app.route("/gallery/<category>", strict_slashes=False)
def gallery(category):
    lang = get_lang()
    return render_template(
        "gallery.html",
        category=category,
        texts=TEXTS[lang],
        lang=lang
    )


# =========================
# FOTO INDIVIDUAL
# =========================
@app.route("/photo/<category>/<photo_id>", strict_slashes=False)
def photo(category, photo_id):
    lang = get_lang()
    folder = os.path.join("static", "images", category)

    related_photos = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith(".jpg") and f != f"{photo_id}.jpg":
                related_photos.append(f.replace(".jpg", ""))

    return render_template(
        "photo.html",
        category=category,
        photo_id=photo_id,
        related_photos=related_photos[:4],
        texts=TEXTS[lang],
        lang=lang,
        meta_description=f"{category.capitalize()} wildlife photograph available for licensing and fine art prints."
    )


# =========================
# ARRANQUE LOCAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
