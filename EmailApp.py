# app.py - Complete Flask Gmail Application

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import Flask, render_template, url_for, request
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from gensim import models
from keras.callbacks import ModelCheckpoint
from keras.layers import Dense, Dropout, Reshape, Flatten, concatenate, Input, Conv1D,LSTM, GlobalMaxPooling1D, Embedding,Bidirectional

from keras.models import Sequential
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.models import Model
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import os
import collections
import re
import string
import matplotlib.pyplot as plt
import pickle
import nltk
from nltk import word_tokenize, WordNetLemmatizer
import requests
nltk.download('punkt_tab')

from flask import Flask, render_template, request
import re
FASTAPI_URL = "http://127.0.0.1:8000/signup"
phishing_urls = [
    "paypal.account-verification-alert.com",
    "appleid.apple.com.account-recovery.support",
    "login-facebook.com.security-check.info",
    "bankofamerica.com.secure-login-update.net",
    "amazon.order-refund-support.info",
    "netflix-membership-verification.com",
]       
def remove_punct(text):
    text_nopunct = ''
    text_nopunct = re.sub('['+string.punctuation+']', '', text)
    return text_nopunct
def lower_token(tokens): 
    return [w.lower() for w in tokens]
def remove_stop_words(tokens): 
    return [word for word in tokens if word not in stoplist]
with open('tokenizer.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
MAX_SEQUENCE_LENGTH = 30
EMBEDDING_DIM = 300
from nltk.corpus import stopwords
stoplist = stopwords.words('english')
def predictsentiment(inputtext):
    cleantext = [remove_punct(inputtext)]
    
    tokens = [word_tokenize(sen) for sen in cleantext] 
    lower_tokens = [lower_token(token) for token in tokens] 
    from nltk.corpus import stopwords
    stoplist = stopwords.words('english')
    filtered_words = [remove_stop_words(sen) for sen in lower_tokens]
    result = [' '.join(sen) for sen in filtered_words] 
    test_sequence = tokenizer.texts_to_sequences(result)
    test_data = pad_sequences(test_sequence, maxlen=MAX_SEQUENCE_LENGTH)
    Y_pred = modelsinfo.predict(test_data)
    Y_pred_classes = np.argmax(Y_pred,axis = 1)
    return Y_pred_classes
    
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gmail.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
import tensorflow as tf
modelsinfo = tf.keras.models.load_model('finalmodel.h5')
# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sent_emails = db.relationship('Email', foreign_keys='Email.sender_id', backref='sender', lazy=True)
    received_emails = db.relationship('Email', foreign_keys='Email.receiver_id', backref='receiver', lazy=True)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_starred = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    is_deleted_sender = db.Column(db.Boolean, default=False)
    is_deleted_receiver = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(20), default='primary')  # primary, social, promotions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'from': self.sender.email,
            'subject': self.subject,
            'content': self.content,
            'date': self.created_at.strftime('%b %d'),
            'is_read': self.is_read,
            'is_starred': self.is_starred,
            'is_spam': self.is_spam,
            'category': self.category
        }

# Initialize database
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('inbox'))
    return redirect(url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_password'] = password
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('inbox'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        response = requests.post(
        FASTAPI_URL,
        data={
            "username": email,
            "password": password
                }
            )

        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('signin'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('signin'))
FASTAPI_LOGIN_URL = "http://127.0.0.1:8000/login"
@app.route('/MyDrive')
def MyDrive():
    email=session['user_email']
    password=session['user_password']
    response = requests.post(
        FASTAPI_LOGIN_URL,
        data={
            "username": email,
            "password": password
        },
        allow_redirects=False 
    )

    # Handle redirect from FastAPI
    if response.status_code == 302:
        flask_response = redirect("http://127.0.0.1:8000/upload")

        # Forward cookie from FastAPI → Flask
        if "set-cookie" in response.headers:
            flask_response.headers["Set-Cookie"] = response.headers["set-cookie"]

        return flask_response

    # Otherwise show error page
    return response.text
   

@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    category = request.args.get('category', 'primary')
    
    # Get all inbox emails (not deleted, not spam)
    emails = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category=category
    ).order_by(Email.created_at.desc()).all()
    
    # Count unread emails
    unread_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        is_read=False
    ).count()
    
    # Count spam emails
    spam_count = Email.query.filter_by(
        receiver_id=user_id,
        is_spam=True,
        is_deleted_receiver=False
    ).count()
    
    # Count by category
    primary_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='primary',
        is_read=False
    ).count()
    
    social_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='social',
        is_read=False
    ).count()
    
    promotions_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='promotions',
        is_read=False
    ).count()
    
    messages = [email.to_dict() for email in emails]
    
    return render_template('inbox.html', 
                         messages=messages, 
                         current_category=category,
                         unread_count=unread_count,
                         spam_count=spam_count,
                         primary_count=primary_count,
                         social_count=social_count,
                         promotions_count=promotions_count)

@app.route('/sent')
def sent():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    
    # Get all sent emails (not deleted)
    emails = Email.query.filter_by(
        sender_id=user_id,
        is_deleted_sender=False
    ).order_by(Email.created_at.desc()).all()
    
    messages = []
    for email in emails:
        messages.append({
            'id': email.id,
            'from': f'To: {email.receiver.email}',
            'subject': email.subject,
            'content': email.content,
            'date': email.created_at.strftime('%b %d'),
            'is_starred': email.is_starred
        })
    
    
    return render_template('sent.html', messages=messages)

@app.route('/spam')
def spam():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    
    # Get all spam emails
    emails = Email.query.filter_by(
        receiver_id=user_id,
        is_spam=True,
        is_deleted_receiver=False
    ).order_by(Email.created_at.desc()).all()
    
    messages = [email.to_dict() for email in emails]
    
    return render_template('spam.html', messages=messages)
@app.route('/email/view/<int:email_id>')
def view_email(email_id):
    email = Email.query.get_or_404(email_id)   # adjust model name
    email.is_read = True
    user_id = session['user_id']
    if user_id not in [email.sender_id, email.receiver_id]:
        abort(403)

    # mark as read
    if not email.is_read and user_id == email.receiver_id:
        email.is_read = True
        db.session.commit()

    sender = User.query.get(email.sender_id)
    category = request.args.get('category', 'primary')
    
    # Get all inbox emails (not deleted, not spam)
    emails = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category=category
    ).order_by(Email.created_at.desc()).all()
    
    # Count unread emails
    unread_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        is_read=False
    ).count()
    
    # Count spam emails
    spam_count = Email.query.filter_by(
        receiver_id=user_id,
        is_spam=True,
        is_deleted_receiver=False
    ).count()
    
    # Count by category
    primary_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='primary',
        is_read=False
    ).count()
    
    social_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='social',
        is_read=False
    ).count()
    
    promotions_count = Email.query.filter_by(
        receiver_id=user_id,
        is_deleted_receiver=False,
        is_spam=False,
        category='promotions',
        is_read=False
    ).count()
    
    messages = [email.to_dict() for email in emails]
    print(sender)
    
   
    return render_template(
        'email_view.html',
        email=email,
        sender=sender,
        messages=messages, 
        current_category=category,
        unread_count=unread_count,
        spam_count=spam_count,
        primary_count=primary_count,
        social_count=social_count,
        promotions_count=promotions_count
    )
   
@app.route('/trash')
def trash():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    
    # Get all deleted emails
    emails = Email.query.filter(
        db.or_(
            db.and_(Email.receiver_id == user_id, Email.is_deleted_receiver == True),
            db.and_(Email.sender_id == user_id, Email.is_deleted_sender == True)
        )
    ).order_by(Email.created_at.desc()).all()
    
    messages = []
    for email in emails:
        if email.receiver_id == user_id:
            messages.append({
                'id': email.id,
                'from': email.sender.email,
                'subject': email.subject,
                'content': email.content,
                'date': email.created_at.strftime('%b %d')
            })
        else:
            messages.append({
                'id': email.id,
                'from': f'To: {email.receiver.email}',
                'subject': email.subject,
                'content': email.content,
                'date': email.created_at.strftime('%b %d')
            })
    
    return render_template('trash.html', messages=messages)

@app.route('/starred')
def starred():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    
    # Get all starred emails
    emails = Email.query.filter_by(
        receiver_id=user_id,
        is_starred=True,
        is_deleted_receiver=False,
        is_spam=False
    ).order_by(Email.created_at.desc()).all()
    
    messages = [email.to_dict() for email in emails]
    
    return render_template('starred.html', messages=messages)

@app.route('/emailcompose', methods=['POST'])
def email_compose():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    sender_id = session['user_id']
    to_email = request.form.get('toemail')
    subject = request.form.get('subject')
    content = request.form.get('message')
    category = request.form.get('category', 'primary')
    data=[content]
    spam_is_spam=False
    for url in phishing_urls:
        if re.search(re.escape(url), content, re.IGNORECASE):
            spam_is_spam=True
    print(data)
   
    my_prediction=predictsentiment(content)
    print(my_prediction)
    if(my_prediction[0]==1):
        spam_is_spam=True
    receiver = User.query.filter_by(email=to_email).first()
    if not receiver:
        flash('Recipient email not found', 'danger')
        return redirect(url_for('inbox'))
    
    new_email = Email(
        sender_id=sender_id,
        receiver_id=receiver.id,
        subject=subject,
        content=content,
        category=category,
        is_spam=spam_is_spam
    )
    
    db.session.add(new_email)
    db.session.commit()
    
    flash('Email sent successfully!', 'success')
    return redirect(url_for('inbox'))

@app.route('/email/delete/<int:email_id>', methods=['POST'])
def delete_email(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    # Mark as deleted for the appropriate user
    if email.receiver_id == user_id:
        email.is_deleted_receiver = True
    elif email.sender_id == user_id:
        email.is_deleted_sender = True
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email moved to trash'})

@app.route('/email/delete-permanent/<int:email_id>', methods=['POST'])
def delete_email_permanent(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    # Check if user has permission
    if email.receiver_id != user_id and email.sender_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Permanently delete
    db.session.delete(email)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email permanently deleted'})

@app.route('/email/restore/<int:email_id>', methods=['POST'])
def restore_email(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    # Restore email
    if email.receiver_id == user_id:
        email.is_deleted_receiver = False
    elif email.sender_id == user_id:
        email.is_deleted_sender = False
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email restored'})

@app.route('/email/star/<int:email_id>', methods=['POST'])
def star_email(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    # Toggle star
    email.is_starred = not email.is_starred
    db.session.commit()
    
    return jsonify({'success': True, 'is_starred': email.is_starred})

@app.route('/email/spam/<int:email_id>', methods=['POST'])
def mark_spam(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    if email.receiver_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Mark as spam
    email.is_spam = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email marked as spam'})

@app.route('/email/not-spam/<int:email_id>', methods=['POST'])
def mark_not_spam(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    if email.receiver_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Unmark spam
    email.is_spam = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email moved to inbox'})

@app.route('/email/read/<int:email_id>', methods=['POST'])
def mark_read(email_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    email = Email.query.get_or_404(email_id)
    
    if email.receiver_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Mark as read
    email.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

# Create sample data (run once)
@app.route('/create-sample-data')
def create_sample_data():
    # Create sample users
    user1 = User.query.filter_by(email='user1@gmail.com').first()
    if not user1:
        user1 = User(
            name='John Doe',
            email='user1@gmail.com',
            password=generate_password_hash('password123')
        )
        db.session.add(user1)
    
    user2 = User.query.filter_by(email='user2@gmail.com').first()
    if not user2:
        user2 = User(
            name='Jane Smith',
            email='user2@gmail.com',
            password=generate_password_hash('password123')
        )
        db.session.add(user2)
    
    db.session.commit()
    
    # Create sample emails
    sample_emails = [
        {
            'sender': user2,
            'receiver': user1,
            'subject': 'Team Meeting Tomorrow',
            'content': 'Don\'t forget we have our quarterly review meeting tomorrow at 10 AM.',
            'category': 'primary'
        },
        {
            'sender': user2,
            'receiver': user1,
            'subject': 'Project Update',
            'content': 'The latest build is ready for testing. All features have been implemented.',
            'category': 'primary',
            'is_starred': True
        },
        {
            'sender': user2,
            'receiver': user1,
            'subject': 'LinkedIn Notification',
            'content': 'You have 5 new connection requests on LinkedIn.',
            'category': 'social'
        },
        {
            'sender': user2,
            'receiver': user1,
            'subject': '50% Off Sale Today!',
            'content': 'Don\'t miss our biggest sale of the year. Use code SAVE50.',
            'category': 'promotions'
        }
    ]
    
    for email_data in sample_emails:
        email = Email(
            sender_id=email_data['sender'].id,
            receiver_id=email_data['receiver'].id,
            subject=email_data['subject'],
            content=email_data['content'],
            category=email_data.get('category', 'primary'),
            is_starred=email_data.get('is_starred', False)
        )
        db.session.add(email)
    
    db.session.commit()
    
    return 'Sample data created! Login with user1@gmail.com / password123'

if __name__ == '__main__':
    app.run(debug=False)