from django.core.cache import cache
from celery import shared_task
from .models import Post

# Example helper to get comment count
def get_post_comment_count(post_uid):
    redis_key = f"post:{post_uid}:commentcount"
    count = cache.get(redis_key)
    return int(count) if count else 0

# Example helper to increment comment count
def increment_post_comment_count(post_uid):
    redis_key = f"post:{post_uid}:commentcount"
    if cache.get(redis_key) is not None:
        cache.incr(redis_key)
    else:
        # Initialize count if it doesn't exist
        cache.set(redis_key, 1, timeout=None)  # Set with no expiration by default

@shared_task
def update_database_comment_counts():
    posts = Post.nodes.all()  # Fetch all posts
    for post in posts:
        # Get the comment count from Redis
        comment_count = get_post_comment_count(post.uid)
        if comment_count is not None:
            post.comment_count = int(comment_count)  # Update the count in the model
            post.save()  # Save the updated count in the database

# Example helper to get like count
def get_post_like_count(post_uid):
    redis_key = f"post:{post_uid}:vibecount"
    count = cache.get(redis_key)
    return int(count) if count else 0

# Example helper to increment like count
def increment_post_like_count(post_uid):
    redis_key = f"post:{post_uid}:vibecount"
    if cache.get(redis_key) is not None:
        cache.incr(redis_key)
    else:
        # Initialize count if it doesn't exist
        cache.set(redis_key, 1, timeout=None)  # Set with no expiration by default
        print("key setup")

@shared_task
def update_database_like_counts():
    posts = Post.nodes.all()  # Fetch all posts
    for post in posts:
        # Get the like count from Redis
        like_count = get_post_like_count(post.uid)
        if like_count is not None:
            post.vibes_count = int(like_count)  # Update the like count in the model
            post.save()  # Save the updated count in the database
