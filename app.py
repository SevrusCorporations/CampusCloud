# Author - SirSevrus (https://github.com/sevruscorporations)

import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

@app.route('/')
def index():
    title = "CampusCloud"
    return render_template('index.html', title=title)

if __name__ == '__main__':
    app.run(debug=True)