from flask import Flask, render_template, request
from pytesseract import *
from PIL import Image, ImageOps
import requests
from webApp import app


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
    current_balloon = None

    for i in range(num_boxes):
        if int(ocr_data["conf"][i]) > 65:  # Adjust confidence threshold as needed
            left = int(ocr_data["left"][i])
            top = int(ocr_data["top"][i])
            width = int(ocr_data["width"][i])
            height = int(ocr_data["height"][i])
            text = ocr_data["text"][i]

            if current_balloon is None:
                current_balloon = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                    "text": text,
                }
            elif abs(top - current_balloon["top"]) < 50:
                current_balloon["text"] += " " + text
                current_balloon["width"] = left + width - current_balloon["left"]
                current_balloon["height"] = max(current_balloon["height"], height)
            else:
                manga_balloons.append(current_balloon)
                current_balloon = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                    "text": text,
                }

    if current_balloon is not None:
        manga_balloons.append(current_balloon)

    for x in range(len(manga_balloons) // 2):
        for i, balloon in enumerate(manga_balloons):
            if i + 1 < len(manga_balloons):
                if abs(balloon["left"] - manga_balloons[i + 1]["left"] < 5) and abs(
                    balloon["top"] - manga_balloons[i + 1]["top"] < 250
                ):
                    balloon["text"] += manga_balloons[i + 1]["text"] + "\n  "
                    balloon["width"] = max(
                        balloon["width"], manga_balloons[i + 1]["width"]
                    )
                    balloon[height] = (
                        max(balloon["height"], manga_balloons[i + 1]["height"]) + 100
                    )
                    manga_balloons.pop(i + 1)

    for balloon in manga_balloons:
        lines = balloon["text"].split("\n")
        span_text = "<br>".join(lines)
        span_style = f"position: absolute; left: {balloon['left']}px; top: {balloon['top']}px; background-color: #FFFF00; padding: 5px; display: inline-block; white-space: nowrap; width: {balloon['width'] + 100}px; height: {balloon['height'] + 100}px;"
        html_output += (
            f'<span class="manga-balloon" style="{span_style}">{span_text}</span>\n'
        )

    image_tag = f'<img src="{url}" alt="Comic Image">'
    html_output = f'<div style="position: relative;">{image_tag}\n{html_output}</div>'

    return html_output
