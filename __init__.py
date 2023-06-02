from flask import Flask
from pytesseract import *
import socket

socket.setdefaulttimeout(9999999)

app = Flask(__name__)
from webApp import routes
