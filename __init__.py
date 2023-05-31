from flask import Flask, render_template, request
from pytesseract import *
from PIL import Image, ImageOps
import requests
import os

app = Flask(__name__)

from webApp import routes
