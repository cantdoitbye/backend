import http.server
import socketserver
import os
import json
import random
from datetime import datetime, timedelta
import uuid

PORT = 8000

# Mock data generation
INTERESTS = [
    'technology', 'programming', 'ai', 'machine learning', 'data science',
    'web development', 'mobile apps', 'cybersecurity', 'cloud computing',
    'blockchain', 'gaming', 'esports', 'virtual reality', 'augmented reality',
    'iot', 'robotics', 'automation', 'big data', 'analytics', 'devops'
]

CONTENT_TYPES = ['post', 'article', 'tutorial', 'video', 'podcast', 'webinar', 'event']

# Generate more realistic user names and interests
USER_NAMES = [
    'Alex Johnson', 'Taylor Smith', 'Jordan Williams', 'Casey Brown', 'Riley Davis',
    'Morgan Wilson', 'Jamie Taylor', 'Quinn Anderson', 'Avery Thomas', 'Skylar Jackson',
    'Peyton White', 'Dakota Harris', 'Remy Martin', 'Sam Carter', 'Robin Lee'
]

# Generate mock users with more realistic data
def generate_users(count=20):
    users = []
    for i in range(count):
        # More focused interests with some common patterns
        primary_interest = random.choice(INTERESTS)
        related_interests = [i for i in INTERESTS if i != primary_interest]
        user_interests = [primary_interest] + random.sample(
            related_interests, 
            k=random.randint(2, 5)
        )
        
        # More realistic user data
        join_date = datetime.now() - timedelta(days=random.randint(1, 365))
        last_active = join_date + timedelta(days=random.randint(1, 30))
        
        users.append({
            'id': i + 1,
            'username': f'user{i + 1}',
            'name': random.choice(USER_NAMES) + (' ' + random.choice(USER_NAMES).split()[-1] if random.random() > 0.3 else ''),
            'email': f'user{i + 1}@example.com',
            'interests': user_interests,
            'join_date': join_date.isoformat(),
            'last_active': last_active.isoformat(),
            'engagement_score': random.uniform(0.3, 0.95),  # How active the user is
            'content_preferences': {
                'preferred_types': random.sample(CONTENT_TYPES, k=random.randint(1, 3)),
                'time_spent': random.randint(5, 120)  # Average minutes per session
            }
        })
    return users

# Content generation helpers
CONTENT_TITLES = {
    'post': ['My Thoughts on {topic}', 'Why {topic} Matters', 'The Future of {topic}', 
             'Lessons from {topic}', '{topic}: A Personal Reflection'],
    'article': ['Comprehensive Guide to {topic}', 'The Science Behind {topic}', 
               'Understanding {topic}: A Deep Dive', 'Best Practices for {topic}'],
    'tutorial': ['Getting Started with {topic}', 'Step-by-Step {topic} Tutorial', 
                'Mastering {topic} in 30 Days', '{topic} for Beginners'],
    'video': ['{topic} Explained', 'The Truth About {topic}', 
             'How to Master {topic}', '{topic} Tips and Tricks'],
    'podcast': ['{topic} Uncovered', 'The {topic} Show', 
               'Deep Dive: {topic}', '{topic} Roundtable Discussion']
}

def generate_content(users, count=200):
    content = []
    trending_topics = random.sample(INTERESTS, 5)  # Some topics are trending more
    
    for i in range(count):
        content_type = random.choice(CONTENT_TYPES)
        author = random.choice(users)
        
        # More realistic content distribution - some topics are more popular
        if random.random() > 0.3:  # 70% chance to use a trending topic
            primary_topic = random.choice(trending_topics)
        else:
            primary_topic = random.choice(INTERESTS)
            
        # Generate related tags
        tags = [primary_topic] + random.sample(
            [t for t in INTERESTS if t != primary_topic], 
            k=random.randint(1, 4)
        )
        
        # Generate realistic title based on content type
        title_template = random.choice(CONTENT_TITLES.get(content_type, ['{topic}']))
        title = title_template.format(topic=primary_topic.title())
        
        # More realistic timestamp distribution (more recent content is more likely)
        days_ago = int(random.expovariate(0.2))  # Exponential distribution
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        timestamp = (datetime.now() - timedelta(
            days=days_ago,
            hours=hours_ago,
            minutes=minutes_ago
        )).isoformat()
        
        # Engagement metrics
        base_engagement = random.uniform(0.1, 0.9)  # Base engagement score
        
        # Content gets more engagement if it matches trending topics
        engagement_boost = 0.3 if primary_topic in trending_topics else 0
        
        # Calculate final engagement score with some randomness
        engagement_score = min(1.0, base_engagement + engagement_boost + random.uniform(-0.1, 0.1))
        
        # Generate view count based on engagement and time since posting
        time_decay = max(0, 1 - (days_ago / 30))  # Linear decay over 30 days
        view_count = int(1000 * engagement_score * time_decay * random.uniform(0.8, 1.2))
        
        # Generate likes and comments based on views
        like_ratio = random.uniform(0.05, 0.15)  # 5-15% of viewers like
        comment_ratio = random.uniform(0.01, 0.05)  # 1-5% of viewers comment
        
        likes = int(view_count * like_ratio)
        comments = int(view_count * comment_ratio)
        
        # Calculate content quality score (0-1)
        quality_score = random.uniform(0.3, 0.95)
        
        # Calculate trending score based on engagement and recency
        recency_score = 1 / (1 + days_ago)  # Higher for more recent content
        trending_score = (engagement_score * 0.6) + (recency_score * 0.4)
        
        # Calculate personalization score (will be calculated per user)
        personalization_score = 0.0
        
        content.append({
            'id': str(uuid.uuid4()),
            'type': content_type,
            'title': title,
            'author': author,
            'timestamp': timestamp,
            'tags': tags,
            'content': f"This is a sample {content_type} about {', '.join(tags)}. "
                      f"Posted by {author['name']} on {timestamp}",
            'engagement': {
                'views': view_count,
                'likes': likes,
                'comments': comments,
                'shares': int(likes * random.uniform(0.1, 0.3)),  # 10-30% of likes
                'bookmarks': int(view_count * random.uniform(0.01, 0.05))  # 1-5% of views
            },
            'metrics': {
                'quality_score': quality_score,
                'engagement_score': engagement_score,
                'trending_score': trending_score,
                'personalization_score': personalization_score,  # Will be calculated per user
                'click_through_rate': random.uniform(0.01, 0.15),  # 1-15%
                'time_spent': random.randint(30, 600)  # seconds
            }
        })
    return content

# Generate connections between users
def generate_connections(users, avg_connections=5):
    connections = {}
    for user in users:
        num_connections = max(1, int(random.gauss(avg_connections, 2)))
        other_users = [u for u in users if u['id'] != user['id']]
        connections[user['id']] = random.sample(
            other_users, 
            min(num_connections, len(other_users))
        )
    return connections

# Generate mock data
# Generate more users and content for richer data
MOCK_USERS = generate_users(50)  # Increased from 20 to 50 users
MOCK_CONTENT = generate_content(MOCK_USERS, 1000)  # Increased from 200 to 1000 content items
MOCK_CONNECTIONS = generate_connections(MOCK_USERS, avg_connections=10)  # More connections per user

PORT = 8000

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/generate_feed':
            self.handle_generate_feed()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/generate_feed':
            self.handle_generate_feed()
        else:
            self.send_error(404, "Not Found")

    def handle_generate_feed(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Mock response
        response = {
            'success': True,
            'feed': [
                {
                    'id': 1,
                    'title': 'Sample Feed Item',
                    'type': 'post',
                    'score': 0.85,
                    'scores': {
                        'interest': 0.4,
                        'connection': 0.3,
                        'time': 0.15
                    },
                    'tags': ['sample', 'test'],
                    'author': 1,
                    'timestamp': '2023-09-11T10:00:00Z'
                }
            ],
            'composition': {
                'personal_connections': 0.4,
                'interest_based': 0.3,
                'trending': 0.15,
                'discovery': 0.1,
                'community': 0.05
            }
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(current_dir, 'templates')
        
        # Check if templates directory exists
        if not os.path.exists(templates_dir):
            print(f"Error: Templates directory not found at {templates_dir}")
            print("Creating templates directory...")
            os.makedirs(templates_dir, exist_ok=True)
        
        # Check if playground.html exists in templates
        playground_path = os.path.join(templates_dir, 'playground.html')
        if not os.path.exists(playground_path):
            print(f"Error: playground.html not found in {templates_dir}")
            print("Copying playground.html to templates directory...")
            import shutil
            src_path = os.path.join(current_dir, 'playground.html')
            if os.path.exists(src_path):
                shutil.copy2(src_path, templates_dir)
                print("playground.html copied to templates directory")
            else:
                print(f"Error: Could not find {src_path}")
                exit(1)
        
        # Change to templates directory
        os.chdir(templates_dir)
        
        # Try to start the server
        print(f"Starting server at http://localhost:{PORT}")
        print(f"Serving files from: {os.getcwd()}")
        
        with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
            print(f"Server started successfully on port {PORT}")
            print("Press Ctrl+C to stop the server")
            print(f"Access the playground at: http://localhost:{PORT}/playground.html")
            httpd.serve_forever()
            
    except PermissionError:
        print(f"Error: Permission denied. Port {PORT} might be in use by another application.")
        print("Try using a different port by setting the PORT environment variable.")
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure no other application is using port 8000")
        print("2. Try running the server on a different port: `set PORT=8080 && python serve.py`")
        print("3. Check if Python has network access through Windows Firewall")
        print("4. Try running the command prompt as Administrator")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
