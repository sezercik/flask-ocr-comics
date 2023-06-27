from flask import Flask, render_template, request
from pytesseract import *
from PIL import Image, ImageOps
import requests
from bs4 import BeautifulSoup
from io import BytesIO


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["POST", "GET"])
def extract():
    error = None
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            error = "URL is required"
            return render_template("index.html", error=error)
        language = request.form.get("language")
        ocr_type = request.form.get("type")
        page = request.form.get("page")
        if page is None or int(page) < 1:
            page = 1

        pages = getPages(url, language, ocr_type, int(page))
        return render_template(
            "extract.html",
            pages=pages,
            current_page=int(page),
            last_page=len(pages),
            extra={"url": url, "language": language, "type": ocr_type},
        )

    return render_template(
        "extract.html",
        pages=pages,
        current_page=int(page),
        last_page=len(pages),
        extra={"url": url, "language": language, "type": ocr_type},
    )


def getPages(url, lang, psm, page):
    urls = getImageUrls(url)
    images_per_page = 10
    start_index = (page - 1) * images_per_page
    end_index = start_index + images_per_page
    page_urls = urls[start_index:end_index]

    pages = []
    for url in page_urls:
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        rgbimg = ImageOps.grayscale(img)

        ocr_data = pytesseract.image_to_data(
            rgbimg,
            lang=lang,
            config="--psm " + psm,
            output_type=pytesseract.Output.DICT,
        )

        num_boxes = len(ocr_data["text"])
        manga_balloons = []
        current_balloon = None
        cumulative_top = 0
        for i in range(num_boxes):
            if int(ocr_data["conf"][i]) > 75:  # Adjust confidence threshold as needed
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
                    cumulative_top += current_balloon["top"]
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
                    if (
                        abs(balloon["left"] - manga_balloons[i + 1]["left"]) < 5
                        and abs(balloon["top"] - manga_balloons[i + 1]["top"]) < 250
                    ):
                        balloon["text"] += manga_balloons[i + 1]["text"] + "\n  "
                        balloon["width"] = max(
                            balloon["width"], manga_balloons[i + 1]["width"]
                        )
                        balloon["height"] = (
                            max(balloon["height"], manga_balloons[i + 1]["height"])
                            + 100
                        )
                        manga_balloons.pop(i + 1)

        image_data = {
            "image": url,
            "text": [],
        }

        # for balloon in manga_balloons[::-1]:
        #     cumulative_top += balloon["top"]
        #     balloon["top"] = cumulative_top
        #     print(balloon["text"], " : ", balloon["top"])

        for balloon in manga_balloons:
            lines = balloon["text"].split("\n")
            span_text = "<br>".join(lines)
            span_style = f"font-family: Anime Ace; font-size: calc(3px + 1vw); top: {balloon['top']}px; left: {balloon['left']}px;  position: absolute; background: darkgray; width: {balloon['width'] + 100}px; height: {balloon['height'] + 100}px;"
            image_data["text"].append({"text": span_text, "style": span_style})

        print(manga_balloons)
        print(image_data)
        pages.append(image_data)
    return pages


def getImageUrls(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")
    urls = []
    for img in img_tags:
        short = img["src"]
        if (
            ".webp" in short or ".jpg" in short or ".png" in short or ".jpeg" in short
        ) and "logo" not in short:
            urls.append(img["src"])

    return urls
