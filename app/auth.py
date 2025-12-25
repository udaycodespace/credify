"""Authentication utilities and decorators"""
from functools import wraps
from flask import session, redirect, url_for, flash
import logging

logging.basicConfig(level=logging.INFO)


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """Decorator to require specific role for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                flash('Please login to access this page', 'warning')
                return redirect(url_for('login'))
            
            # Check user role
            user_role = session.get('role')
            if user_role != role:
                logging.info(f"Access denied for user {session.get('username', 'unknown')} (role: {user_role}) trying to access {role}-only route")
                flash(f'Access denied. This page is only for {role}s', 'danger')
                return redirect(url_for('index'))
            
            logging.debug(f"Access granted to {session.get('username')} ({user_role}) for {role} route")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
