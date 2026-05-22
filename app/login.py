# app/login.py
from flask import render_template, request, redirect, url_for, session
from config import CREDENTIALS


def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == CREDENTIALS["username"]
            and password == CREDENTIALS["password"]
        ):

            session["logged_in"] = True
            session["username"] = username

            return redirect(url_for("dashboard.dashboard"))

        else:
            error = "Username atau password salah"

    return render_template(
        "login.html",
        error=error
    )