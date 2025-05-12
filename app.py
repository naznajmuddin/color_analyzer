from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
)
import os
import json
from werkzeug.utils import secure_filename
from PIL import Image
from analyzer import ImageColorAnalyzer
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from collections import Counter

Image.MAX_IMAGE_PIXELS = 1000000000

app = Flask(__name__)
# app.config["UPLOAD_FOLDER"] = "static/uploads"
# app.config["REPORT_FOLDER"] = "static/reports"
app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
app.config["REPORT_FOLDER"] = "/tmp/reports"
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

# JSON file to persist data
COLOR_DATA_FILE = "color_data.json"

# Load stored data
if os.path.exists(COLOR_DATA_FILE):
    with open(COLOR_DATA_FILE, "r") as f:
        image_hexcode_store = json.load(f)
else:
    image_hexcode_store = {}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    num_colors = int(request.form.get("num_colors", 5))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        image = Image.open(filepath)
        if image.mode == "RGBA":
            image = image.convert("RGB")
            image.save(filepath)

        analyzer = ImageColorAnalyzer(image, num_colors)
        hex_colors, rgb_colors, percentages = analyzer.analyze_colors()

        # Store hex codes
        image_hexcode_store[filename] = hex_colors
        with open(COLOR_DATA_FILE, "w") as f:
            json.dump(image_hexcode_store, f, indent=4)

        colors = [
            {
                "rgb": rgb,
                "hex": hex,
                "percentage": perc,
                "textColor": "#000" if sum(rgb) > 400 else "#FFF",
            }
            for rgb, hex, perc in zip(rgb_colors, hex_colors, percentages)
        ]

        return jsonify(
            {
                "image_url": f"/uploads/{filename}",
                "filename": filename,
                "colors": colors,
            }
        )

    return "Invalid file type", 400


@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    filename = data.get("filename")
    colors = data.get("colors")

    if not filename or not colors:
        return jsonify({"error": "Missing data"}), 400

    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    pdf_filename = f"{filename.rsplit('.', 1)[0]}.pdf"
    pdf_path = os.path.join(app.config["REPORT_FOLDER"], pdf_filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Image Color Analysis Report")

    img_reader = ImageReader(image_path)
    img_width, img_height = Image.open(image_path).size
    aspect = img_width / img_height
    img_display_width = 200
    img_display_height = img_display_width / aspect

    c.drawImage(
        img_reader, 50, height - 300, width=img_display_width, height=img_display_height
    )

    c.setFont("Helvetica", 12)
    y_position = height - 320

    for color in colors:
        hex_code = color["hex"]
        percentage = color["percentage"]
        rgb = color["rgb"]

        c.setFillColorRGB(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
        c.rect(50, y_position, 50, 20, fill=1, stroke=0)

        c.setFillColorRGB(0, 0, 0)
        c.drawString(
            110, y_position + 5, f"Hex: {hex_code}, RGB: {rgb}, {percentage:.2f}%"
        )

        y_position -= 30

    c.save()
    return jsonify({"pdf_url": f"/static/reports/{pdf_filename}"})


@app.route("/view_result/<filename>")
def view_result(filename):
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image = Image.open(image_path)
    analyzer = ImageColorAnalyzer(image, 5)
    hex_colors, rgb_colors, percentages = analyzer.analyze_colors()

    colors = [
        {
            "rgb": rgb,
            "hex": hex,
            "percentage": perc,
            "textColor": "#000" if sum(rgb) > 400 else "#FFF",
        }
        for rgb, hex, perc in zip(rgb_colors, hex_colors, percentages)
    ]

    return render_template(
        "result.html",
        image_url=f"/static/uploads/{filename}",
        filename=filename,
        colors=colors,
    )


@app.route("/common_colors", methods=["GET"])
def common_colors():
    if not image_hexcode_store:
        return jsonify({"message": "No data available"}), 400

    hex_sets = [set(hex_list) for hex_list in image_hexcode_store.values()]
    common_hexes = set.intersection(*hex_sets) if hex_sets else set()

    return jsonify(
        {"common_hex_codes": list(common_hexes), "total_images_analyzed": len(hex_sets)}
    )


@app.route("/usual_colors", methods=["GET"])
def usual_colors():
    all_hexes = []
    for hex_list in image_hexcode_store.values():
        all_hexes.extend(hex_list)

    color_counter = Counter(all_hexes)
    most_common = color_counter.most_common(10)

    return jsonify(
        [{"hex": hex_code, "count": count} for hex_code, count in most_common]
    )


@app.route("/all_images_data", methods=["GET"])
def all_images_data():
    if not image_hexcode_store:
        return jsonify({"message": "No data available"}), 400

    image_data = []
    for filename, hex_colors in image_hexcode_store.items():
        image_data.append(
            {
                "filename": filename,
                "colors": hex_colors,
                "dominant_color": hex_colors[0] if hex_colors else None,
            }
        )

    return jsonify(image_data)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/clear_data", methods=["POST"])
def clear_data():
    global image_hexcode_store
    image_hexcode_store = {}

    with open(COLOR_DATA_FILE, "w") as f:
        json.dump(image_hexcode_store, f, indent=4)

    return jsonify({"message": "Color data cleared successfully"})


if __name__ == "__main__":
    app.run(debug=True)
