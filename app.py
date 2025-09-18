# Author - SirSevrus (https://github.com/sevruscorporations)

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json

from libs.getQueries import get_queries
from libs.matchFiles import match_query

app = Flask(__name__)

QUERIES = None
Queries = None

def init():
    global Queries, QUERIES
    QUERIES = load_queries()
    Queries = get_queries(QUERIES)
    print(QUERIES)
    print(Queries)

def load_queries():
    with open('data/queries.json', 'r') as file:
        queries_json = json.load(file)
    return queries_json

@app.route('/')
def index():
    title = "CampusCloud"
    return render_template('index.html', title=title)

@app.route("/get_url=<query>", methods=["GET"])
def get_url(query):
    matched = match_query(Queries, query)
    return matched

if __name__ == '__main__':
    init()
    app.run(debug=True)