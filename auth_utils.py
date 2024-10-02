# auth_utils.py
from flask import session, redirect, url_for, request
from functools import wraps # for persistent login


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("this is in login")
        print(session)
        if "user_id" not in session:
            return redirect(url_for("user_bp.login"))
        return f(*args, **kwargs)

    return decorated_function
