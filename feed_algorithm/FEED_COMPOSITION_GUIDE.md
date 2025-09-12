# Feed Composition Customization Guide

This guide explains how to customize the feed composition in the Ooumph platform through different interfaces.

## 1. GraphQL API (For End Users)

Users can update their feed composition using the `updateFeedComposition` mutation:

```graphql
mutation {
  updateFeedComposition(
    personalConnections: 0.4,
    interestBased: 0.25,
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

## 2. Django Admin (For Administrators)

Admins can modify feed compositions through the Django admin interface:

1. Access the Django admin panel (typically at `/admin/`)
2. Navigate to "Users" section
3. Click on a user to edit their profile
4. Under the "Feed Composition" section, you can modify:
   - Personal Connections
   - Interest Based
   - Trending Content
   - Discovery Content
   - Community Content
   - Product Content

## 3. Programmatic Access (For Developers)

You can update feed composition programmatically in your Python code:

```python
from feed_algorithm.models import FeedComposition

# Get or create a user's feed composition
composition, created = FeedComposition.objects.get_or_create(user=user)

# Update the composition
composition.personal_connections = 0.4
composition.interest_based = 0.25
composition.trending_content = 0.15
composition.discovery_content = 0.1
composition.community_content = 0.05
composition.product_content = 0.05

try:
    # Save will automatically validate the composition
    composition.save()
    print("Feed composition updated successfully")
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Default Composition Values

| Content Type | Default | Description |
|--------------|---------|-------------|
| Personal Connections | 40% | Content from user's direct connections |
| Interest Based | 25% | Content matching user's interests |
| Trending Content | 15% | Currently popular content |
| Discovery Content | 10% | New or diverse content |
| Community Content | 5% | Content from community channels |
| Product Content | 5% | Promoted or product-related content |

## Important Notes

1. **Validation**: The sum of all composition values must equal 1.0 (100%)
2. **Enforcement**: The system includes validation to ensure this constraint
3. **Admin Interface**: Provides visual feedback if the composition is invalid
4. **Immediate Effect**: Changes take effect immediately for the next feed generation
5. **Caching**: Feed results are cached, so changes might not be immediately visible

## Troubleshooting

- If you receive a validation error, ensure all values sum to 1.0
- Check server logs for detailed error messages
- Verify user permissions when making programmatic changes
- Clear cache if changes don't appear immediately
