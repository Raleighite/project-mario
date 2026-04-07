from flask import render_template
from flask_login import login_required
from app.web import web_bp


@web_bp.route('/')
def index():
    return render_template('main/index.html')


@web_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html')
