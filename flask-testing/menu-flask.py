from flask import Flask, render_template, url_for, flash, redirect
import forms

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd'

hi = [1,2,3,4,5,6]

@app.route("/", methods=["GET", "POST"])
def index():
    form = forms.LoginForm()
    if form.validate_on_submit():
        flash(f"Connecting to {form.pa_ip.data} succeeded..", "success")
        return redirect(url_for('loggedIn'))
    return render_template("index.html", title="gMenu", form=form)

@app.route("/test")
def test():
    return render_template("about.html", title="gAbout",testing=hi)

@app.route("/loggedin")
def loggedIn():
    form = forms.PaPAN()
    return render_template("logged-in.html", title="Connected", form=form, testing=hi)

if __name__ == "__main__":
    app.run(debug=True)