from flask import Flask
from dash import Dash

server = Flask("Natural Disasters Dashboard")
app = Dash(server=server)