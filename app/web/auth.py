from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.web import web_bp
from app.extensions import db
from app.models import User
from app.forms.auth import LoginForm, RegistrationForm


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('web.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('web.dashboard'))
    return render_template('auth/login.html', form=form)


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('web.login'))
    return render_template('auth/register.html', form=form)


@web_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('web.index'))
