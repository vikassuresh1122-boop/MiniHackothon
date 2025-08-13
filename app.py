from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

client = MongoClient(os.environ.get('MONGO_URL'))
db = client['festival_planner']
events_collection = db['events']
bookmarks_collection = db['bookmarks']

sample_events = [
    {
        "name": "Summer Music Festival",
        "date": "2025-08-20",
        "location": "Central Park, New York",
        "description": "A vibrant summer music festival featuring top artists",
        "category": "Music"
    },
    {
        "name": "Food & Wine Festival",
        "date": "2025-09-15",
        "location": "Napa Valley, California",
        "description": "Celebrate culinary excellence with world-class chefs",
        "category": "Food"
    },
    {
        "name": "Art & Culture Festival",
        "date": "2025-10-05",
        "location": "Museum District, Houston",
        "description": "Explore contemporary art and cultural exhibitions",
        "category": "Art"
    },
    {
        "name": "Tech Innovation Summit",
        "date": "2025-11-12",
        "location": "Silicon Valley, California",
        "description": "Discover the latest in technology and innovation",
        "category": "Technology"
    },
    {
        "name": "Holiday Light Festival",
        "date": "2025-12-18",
        "location": "Downtown Seattle, Washington",
        "description": "Magical holiday light displays and winter celebrations",
        "category": "Holiday"
    }
]

def init_database():
    if events_collection.count_documents({}) == 0:
        events_collection.insert_many(sample_events)
        print("Sample data added to database!")

@app.route('/')
def index():
    events = list(events_collection.find().sort("date", 1))
    
    for event in events:
        event['_id'] = str(event['_id'])
    
    return render_template('index.html', events=events)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        event_data = {
            "name": request.form['name'],
            "date": request.form['date'],
            "location": request.form['location'],
            "description": request.form['description'],
            "category": request.form['category']
        }
        events_collection.insert_one(event_data)
        return redirect(url_for('index'))
    
    return render_template('add_event.html')

@app.route('/bookmark/<event_id>')
def bookmark_event(event_id):
    user_id = session.get('user_id', 'anonymous')
    
    existing = bookmarks_collection.find_one({
        "user_id": user_id,
        "event_id": event_id
    })
    
    if not existing:
        bookmarks_collection.insert_one({
            "user_id": user_id,
            "event_id": event_id,
            "bookmarked_at": datetime.datetime.now()
        })
        return jsonify({"status": "bookmarked"})
    else:
        bookmarks_collection.delete_one({
            "user_id": user_id,
            "event_id": event_id
        })
        return jsonify({"status": "unbookmarked"})

@app.route('/my_bookmarks')
def my_bookmarks():
    user_id = session.get('user_id', 'anonymous')
    
    bookmarks = list(bookmarks_collection.find({"user_id": user_id}))
    bookmarked_ids = [ObjectId(b['event_id']) for b in bookmarks]
    
    events = list(events_collection.find({"_id": {"$in": bookmarked_ids}}))
    
    for event in events:
        event['_id'] = str(event['_id'])
    
    return render_template('bookmarks.html', events=events)

@app.route('/set_user/<user_id>')
def set_user(user_id):
    session['user_id'] = user_id
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_database()
    app.run(debug=True)