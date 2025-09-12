# Feed Algorithm Integration

This module integrates the custom feed generation algorithm into the Ooumph backend.

## Features

- Personalized feed generation based on user preferences
- Configurable content distribution (personal, trending, discovery, etc.)
- A/B testing support for feed composition
- Caching layer for improved performance
- Admin interface for managing feed settings

## Models

### UserProfile
Extends the base user model with feed-specific preferences and settings.

### FeedComposition
Defines the content distribution ratios for a user's feed.

## GraphQL API

### Queries

- `myFeedProfile`: Get the current user's feed profile
- `myFeedComposition`: Get the current user's feed composition settings
- `generateFeed(size: Int, refreshCache: Boolean)`: Generate a personalized feed

### Mutations

- `updateFeedProfile`: Update feed profile settings
- `updateFeedComposition`: Update feed composition ratios

## Integration with Algorithm

The module integrates with the custom feed generation algorithm located in `Algo/feed_algorithm/`.

## Configuration

Add the following to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    'feed_algorithm',
]

# Feed Algorithm Settings
FEED_ALGORITHM_CONFIG = {
    'DEFAULT_FEED_SIZE': 20,
    'CACHE_TIMEOUT': 300,  # 5 minutes
    'MAX_CACHE_AGE': 3600,  # 1 hour
}
```

## Dependencies

- Django
- Graphene-Django
- django-graphql-jwt (for authentication)
- Custom feed algorithm from `Algo/feed_algorithm/`

## Setup

1. Add 'feed_algorithm' to INSTALLED_APPS
2. Run migrations: `python manage.py makemigrations feed_algorithm`
3. Apply migrations: `python manage.py migrate`
4. Configure URLs and middleware as needed

## Usage

```graphql
# Generate a feed
query {
  generateFeed(size: 20) {
    success
    message
    items {
      id
      contentType
      contentId
      score
      ranking
      metadata
    }
    totalCount
    hasMore
    composition
    generatedAt
  }
}

# Update feed composition
mutation {
  updateFeedComposition(
    personalConnections: 0.4,
    interestBased: 0.3,
    trendingContent: 0.15,
    discoveryContent: 0.1,
    communityContent: 0.05,
    productContent: 0.05
  ) {
    composition {
      personalConnections
      interestBased
      trendingContent
      discoveryContent
      communityContent
      productContent
    }
    success
    message
  }
}
```

## Testing

Run the test suite with:

```bash
python manage.py test feed_algorithm
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request
