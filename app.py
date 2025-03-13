from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from PIL import Image
from analyzer import ImageColorAnalyzer

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Load image using PIL
            image = Image.open(filepath)

            # Get user-selected options
            num_colors = int(request.form.get("num_colors", 5))

            # Extract colors using ImageColorAnalyzer
            analyzer = ImageColorAnalyzer(image, num_colors)
            hex_colors, rgb_colors, percentages = analyzer.analyze_colors()

            return render_template(
                "index.html",
                filename=filename,
                colors=list(
                    zip(rgb_colors, hex_colors, percentages)
                ),  # Pass RGB, HEX, and % data
                num_colors=num_colors,
            )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
