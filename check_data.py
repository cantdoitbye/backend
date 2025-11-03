#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from user_activity.models import *

print('=== Database Activity Data Analysis ===')
print(f'UserActivity count: {UserActivity.objects.count()}')
print(f'ContentInteraction count: {ContentInteraction.objects.count()}')
print(f'ProfileActivity count: {ProfileActivity.objects.count()}')
print(f'MediaInteraction count: {MediaInteraction.objects.count()}')
print(f'SocialInteraction count: {SocialInteraction.objects.count()}')
print(f'SessionActivity count: {SessionActivity.objects.count()}')
print(f'VibeActivity count: {VibeActivity.objects.count()}')
print(f'ActivityAggregation count: {ActivityAggregation.objects.count()}')

print('\n=== UserActivity Sample ===')
for ua in UserActivity.objects.all()[:2]:
    print(f'{ua.user.username}: {ua.activity_type} at {ua.timestamp}')

print('\n=== ContentInteraction Sample ===')
for ci in ContentInteraction.objects.all()[:3]:
    print(f'{ci.user.username}: {ci.interaction_type} on {ci.content_type}:{ci.content_id} at {ci.timestamp}')

print('\n=== ProfileActivity Sample ===')
for pa in ProfileActivity.objects.all()[:3]:
    print(f'{pa.visitor.username}: {pa.activity_type} on {pa.profile_owner.username} profile at {pa.timestamp}')

print('\n=== SocialInteraction Sample ===')
for si in SocialInteraction.objects.all()[:3]:
    target = si.target_user.username if si.target_user else 'N/A'
    print(f'{si.user.username}: {si.interaction_type} with {target} at {si.timestamp}')

print('\n=== VibeActivity Sample ===')
for va in VibeActivity.objects.all()[:3]:
    print(f'{va.user.username}: {va.activity_type} - {va.vibe_type} vibe {va.vibe_name or va.vibe_id} at {va.timestamp}')

print('\n=== ActivityAggregation Sample ===')
for aa in ActivityAggregation.objects.all():
    print(f'{aa.user.username}: {aa.aggregation_type} for {aa.date} - counts: {aa.activity_counts}')