from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('index.html', name=current_user.username)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.username)