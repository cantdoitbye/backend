# Opportunity Counts Query

## Overview
The `opportunityCounts` query returns counts of different opportunity types in the system.

## Query

```graphql
query GetOpportunityCounts {
  opportunityCounts {
    totalCount
    jobCount
    eventCount
    causeCount
    businessCount
    postCount
  }
}
```

## Response Example

```json
{
  "data": {
    "opportunityCounts": {
      "totalCount": 65,
      "jobCount": 15,
      "eventCount": 10,
      "causeCount": 10,
      "businessCount": 10,
      "postCount": 20
    }
  }
}
```

## Fields

- **totalCount**: Total number of all opportunities (sum of all types)
- **jobCount**: Number of job opportunities (actual count from database)
- **eventCount**: Number of event opportunities (static: 10, not yet implemented)
- **causeCount**: Number of cause opportunities (static: 10, not yet implemented)
- **businessCount**: Number of business opportunities (static: 10, not yet implemented)
- **postCount**: Number of posts (static: 20, not yet implemented)

## Notes

- Only **jobCount** is dynamically calculated from the database
- Event, cause, and business counts are currently static (10 each) as these features are not yet implemented
- Only counts active, non-deleted opportunities
- Requires authentication

## Use Cases

- Dashboard statistics
- Homepage counters
- Analytics displays
- Navigation badges showing available opportunities by type
