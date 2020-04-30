from flask import Flask, render_template, url_for

app = Flask(__name__)

hi = [1,2,3,4,5,6]

@app.route("/")
def home():
    return render_template("index.html", title="gMenu")

@app.route("/test")
def test():
    return render_template("about.html", title="gAbout",testing=hi)

if __name__ == "__main__":
    app.run(debug=True)