from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

@app.route('/')
def landing():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/view')
def view():
    return render_template('view.html')
    
@app.route('/add')
def add():
    return render_template('add.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', debug=True)