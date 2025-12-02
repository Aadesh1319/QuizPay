# QuizPay - Flask Project

## Overview
QuizPay is a small Flask web application where users can register, take 5-question quizzes by subject (Technology, Science, History), and earn ₹100 per correct answer added to an in-app wallet. Admin can add questions and view users & quiz attempts.

## Files
- app.py - main Flask app
- requirements.txt - Python dependencies
- mysql_setup.sql - SQL script to create database and tables
- templates/ - Jinja2 HTML templates
- static/ - CSS files

## Database credentials (exactly as requested)
The app uses `mysql.connector` and connects using:
```py
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
)
