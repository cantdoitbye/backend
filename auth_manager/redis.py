from django.core.cache import cache

def get_otp_count(user_id):
    otp_count_key = f"otp_count_{user_id}"
    count = cache.get(otp_count_key)
    return int(count) if count else 0

def increment_otp_count(user_id):
    otp_count_key = f"otp_count_{user_id}"
    if cache.get(otp_count_key) is not None:
        cache.incr(otp_count_key)
    else:
        # Set count to 1 with a 1-hour expiration if it's the first increment
        cache.set(otp_count_key, 1, timeout=3600)

def store_otp(user_id, otp):
    otp_key = f"otp_{user_id}"
    cache.set(otp_key, otp, timeout=300)  # 5-minute expiration
