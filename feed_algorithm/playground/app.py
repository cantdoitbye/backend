from flask import Flask, render_template, request, jsonify
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Mock data for demonstration
MOCK_USERS = [
    {"id": 1, "username": "user1", "interests": ["tech", "programming"]},
    {"id": 2, "username": "user2", "interests": ["sports", "fitness"]},
    {"id": 3, "username": "user3", "interests": ["tech", "gaming"]},
]

MOCK_CONTENT = [
    {"id": 1, "type": "post", "title": "Introduction to Python", "tags": ["tech", "programming"], "author": 1, "timestamp": "2023-09-10T10:00:00Z"},
    {"id": 2, "type": "post", "title": "Best Workout Routines", "tags": ["sports", "fitness"], "author": 2, "timestamp": "2023-09-11T09:30:00Z"},
    {"id": 3, "type": "event", "title": "Tech Conference 2023", "tags": ["tech", "networking"], "author": 3, "timestamp": "2023-09-12T14:00:00Z"},
    {"id": 4, "type": "post", "title": "Gaming News Update", "tags": ["gaming", "news"], "author": 1, "timestamp": "2023-09-11T16:45:00Z"},
    {"id": 5, "type": "event", "title": "Marathon Training", "tags": ["sports", "fitness"], "author": 2, "timestamp": "2023-09-15T07:00:00Z"},
]

# Mock algorithm implementation
def generate_feed(user_id, composition=None, size=5):
    # Default composition if not provided
    if composition is None:
        composition = {
            'personal_connections': 0.4,
            'interest_based': 0.3,
            'trending': 0.15,
            'discovery': 0.1,
            'community': 0.05
        }
    
    user = next((u for u in MOCK_USERS if u['id'] == user_id), None)
    if not user:
        return []
    
    # Simple scoring function based on user interests and content tags
    feed_items = []
    for item in MOCK_CONTENT:
        score = 0
        
        # Interest-based scoring
        common_interests = set(user.get('interests', [])) & set(item.get('tags', []))
        interest_score = len(common_interests) * 0.3
        
        # Author connection (simplified)
        connection_score = 0.1 if item['author'] in [u['id'] for u in MOCK_USERS if u != user] else 0
        
        # Time decay (newer content gets higher score)
        item_time = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        time_diff = (datetime.now(item_time.tzinfo) - item_time).days
        time_score = max(0, 1 - (time_diff / 30)) * 0.2  # 30-day decay
        
        # Calculate final score with composition weights
        score = (
            connection_score * composition['personal_connections'] +
            interest_score * composition['interest_based'] +
            time_score * composition['trending']
        )
        
        feed_items.append({
            **item,
            'score': round(score, 4),
            'scores': {
                'interest': round(interest_score, 4),
                'connection': round(connection_score, 4),
                'time': round(time_score, 4)
            }
        })
    
    # Sort by score and limit size
    feed_items.sort(key=lambda x: x['score'], reverse=True)
    return feed_items[:size]

@app.route('/')
def index():
    return render_template('index.html', users=MOCK_USERS, content=MOCK_CONTENT)

@app.route('/generate_feed', methods=['POST'])
def api_generate_feed():
    try:
        data = request.get_json()
        user_id = int(data.get('user_id', 1))
        size = int(data.get('size', 5))
        
        # Get composition from request or use defaults
        composition = {
            'personal_connections': float(data.get('personal_connections', 0.4)),
            'interest_based': float(data.get('interest_based', 0.3)),
            'trending': float(data.get('trending', 0.15)),
            'discovery': float(data.get('discovery', 0.1)),
            'community': float(data.get('community', 0.05))
        }
        
        # Ensure composition sums to 1
        total = sum(composition.values())
        if abs(total - 1.0) > 0.01:  # Allow for small floating point errors
            composition = {k: v/total for k, v in composition.items()}
        
        feed = generate_feed(user_id, composition, size)
        return jsonify({
            'success': True,
            'feed': feed,
            'composition': composition
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create static directory for CSS/JS if it doesn't exist
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, port=5000)
