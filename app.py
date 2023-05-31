from flask import Flask, render_template, request
from pytesseract import *
from PIL import Image, ImageOps
import requests
import os

app = Flask(__name__, static_url_path="/static")

env_config = os.getenv("PROD_APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/proccess", methods=["POST"])
def proccess():
    error = None
    if request.method == "POST":
        sonuc = getText(
            request.form["url"], request.form["language"], request.form["type"]
        )
        return render_template("index.html", sonuc=sonuc)
    else:
        error = "url girmediniz"
        return render_template("proccess.html", error=error)


def getText(url, lang, psm):
    print(url)
    img = Image.open(
        requests.get(
            url,
            stream=True,
        ).raw
    )
    rgbimg = Image.new("RGBA", img.size)
    rgbimg = ImageOps.grayscale(rgbimg)
    rgbimg.paste(img)
    img = Image.open(requests.get(url, stream=True).raw)
    rgbimg = ImageOps.grayscale(img)

    ocr_data = pytesseract.image_to_data(
        rgbimg,
        lang=lang,
        config="--psm " + psm,
        output_type=pytesseract.Output.DICT,
    )

    html_output = ""
    num_boxes = len(ocr_data["text"])
    manga_balloons = []
    same_line_text = ""
    max_word_width = 0  # Maximum word width for a line
    print(ocr_data)
    for i in range(num_boxes):
        if int(ocr_data["conf"][i]) > 65:  # Adjust confidence threshold as needed
            left = int(ocr_data["left"][i])
            top = int(ocr_data["top"][i])
            width = int(ocr_data["width"][i])
            height = int(ocr_data["height"][i])
            text = ocr_data["text"][i]

            if len(manga_balloons) > 0 and top - manga_balloons[-1]["top"] < 5:
                same_line_text += " " + text
                max_word_width = max(max_word_width, width)
            else:
                if same_line_text:
                    manga_balloons[-1]["text"] += " " + same_line_text
                    manga_balloons[-1]["width"] = max_word_width
                    same_line_text = ""
                    max_word_width = 0
                manga_balloons.append(
                    {
                        "left": left,
                        "top": top,
                        "height": height,
                        "text": text,
                        "width": width,
                    }
                )

    # Combine same line text from the last manga balloon, if any
    if same_line_text:
        manga_balloons[-1]["text"] += " " + same_line_text
        manga_balloons[-1]["width"] = max_word_width

    # Create a single span tag for each manga balloon
    for balloon in manga_balloons:
        span_text = balloon["text"].replace("<", "&lt;").replace(">", "&gt;")
        span_style = f"position: absolute; left: {balloon['left']}px; top: {balloon['top']}px; background-color: #FFFF00; padding: 5px; display: inline-block; white-space: nowrap; width: {balloon['width'] + 100}px; height: {balloon['height']}px;"
        html_output += (
            f'<span class="manga-balloon" style="{span_style}">{span_text}</span>\n'
        )

    # Add image tag
    image_tag = f'<img src="{url}" alt="Comic Image">'
    html_output = f'<div style="position: relative;">{image_tag}\n{html_output}</div>'

    return html_output
