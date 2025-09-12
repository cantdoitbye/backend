""
Visualization tool for the feed algorithm.
This script generates visual representations of feed data.
"""
import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from feed_algorithm.models import FeedComposition

User = get_user_model()

class FeedVisualizer:
    """Visualizes feed algorithm output and statistics."""
    
    def __init__(self):
        self.fig_size = (12, 8)
        self.colors = {
            'personal_connections': '#4285F4',
            'interest_based': '#EA4335',
            'trending_content': '#FBBC05',
            'discovery_content': '#34A853',
            'community_content': '#673AB7',
            'product_content': '#FF5722'
        }
    
    def plot_feed_composition(self, composition_data, title='Feed Composition'):
        """Plot a pie chart of feed composition."""
        labels = []
        sizes = []
        colors = []
        
        for key, value in composition_data.items():
            if key in self.colors and value > 0:
                labels.append(key.replace('_', ' ').title())
                sizes.append(value)
                colors.append(self.colors[key])
        
        plt.figure(figsize=self.fig_size)
        plt.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={
                'edgecolor': 'white',
                'linewidth': 1
            }
        )
        
        plt.title(title, fontsize=16, pad=20)
        plt.axis('equal')
        plt.tight_layout()
        
        # Save the figure
        filename = f'feed_composition_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved composition chart as {filename}")
        return filename
    
    def plot_feed_items(self, feed_items, title='Feed Items'):
        """Plot a bar chart of feed items with their scores."""
        if not feed_items:
            print("No feed items to visualize.")
            return
        
        # Prepare data
        item_ids = [f"{item['contentType']}-{item['contentId']}" for item in feed_items]
        scores = [item['score'] for item in feed_items]
        content_types = [item['contentType'] for item in feed_items]
        
        # Create a color map based on content type
        unique_types = list(set(content_types))
        type_colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
        color_map = {t: type_colors[i] for i, t in enumerate(unique_types)}
        colors = [color_map[t] for t in content_types]
        
        plt.figure(figsize=(max(10, len(item_ids) * 0.8), 6))
        
        # Create bars
        bars = plt.bar(item_ids, scores, color=colors)
        
        # Add score labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.01,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                rotation=45
            )
        
        # Customize the plot
        plt.title(title, fontsize=16, pad=20)
        plt.xlabel('Content Items', fontsize=12)
        plt.ylabel('Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add legend for content types
        legend_handles = [
            plt.Rectangle((0,0), 1, 1, color=color, label=ctype)
            for ctype, color in color_map.items()
        ]
        plt.legend(
            handles=legend_handles, 
            title='Content Types',
            bbox_to_anchor=(1.05, 1), 
            loc='upper left'
        )
        
        plt.tight_layout()
        
        # Save the figure
        filename = f'feed_items_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved items chart as {filename}")
        return filename
    
    def plot_user_comparison(self, user_data):
        """Compare feed compositions across different users."""
        if not user_data:
            print("No user data provided for comparison.")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Prepare data for stacked bar chart
        categories = list(self.colors.keys())
        x = np.arange(len(user_data))
        width = 0.8
        bottom = np.zeros(len(user_data))
        
        for i, category in enumerate(categories):
            values = [data['composition'].get(category, 0) for data in user_data.values()]
            plt.bar(
                x, 
                values, 
                width, 
                bottom=bottom,
                label=category.replace('_', ' ').title(),
                color=self.colors[category]
            )
            bottom += values
        
        # Customize the plot
        plt.title('Feed Composition Comparison', fontsize=16, pad=20)
        plt.xlabel('Users', fontsize=12)
        plt.ylabel('Composition Ratio', fontsize=12)
        plt.xticks(x, user_data.keys(), rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save the figure
        filename = f'user_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved user comparison chart as {filename}")
        return filename

def visualize_feed_from_file(filename):
    """Visualize feed data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            feed_data = json.load(f)
        
        visualizer = FeedVisualizer()
        
        # Visualize composition
        if 'composition' in feed_data:
            visualizer.plot_feed_composition(
                feed_data['composition'],
                title='Feed Composition Analysis'
            )
        
        # Visualize items
        if 'items' in feed_data and feed_data['items']:
            visualizer.plot_feed_items(
                feed_data['items'],
                title='Feed Items with Scores'
            )
        
        print("Visualization complete! Check the generated image files.")
        
    except Exception as e:
        print(f"Error visualizing feed data: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize feed algorithm output')
    parser.add_argument('--file', type=str, help='JSON file containing feed data')
    
    args = parser.parse_args()
    
    if args.file:
        visualize_feed_from_file(args.file)
    else:
        print("Please provide a JSON file with feed data using the --file argument.")
        print("Example: python visualize_feed.py --file feed_output.json")
