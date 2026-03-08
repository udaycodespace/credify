import sys
sys.path.insert(0, r'C:\Users\uday2\TOOLS\credify')
from app.app import app
from app.models import db, User

with app.app_context():
    students = User.query.filter_by(role='student').all()
    if not students:
        print("No student accounts found in the database.")
    for s in students:
        print(f"DB student_id='{s.student_id}' | username='{s.username}' | email='{s.email}' | onboarding='{s.onboarding_status}'")
