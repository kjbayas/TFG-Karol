from functools import wraps
from flask import redirect, session

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'login' not in session:
            return redirect('/admin/login')
        return func(*args, **kwargs)
    return wrapper
