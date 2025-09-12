# Algo Directory Usage Summary

## Overview
This document summarizes how the `Algo` directory is being used throughout the Ooumph project.

## Core Integration
- **Location**: `ooumph-backend/feed_algorithm/`
- **Main Components**:
  - `FeedAlgorithmEngine`: Core engine for feed generation
  - `FeedGenerationService`: Handles feed generation logic

## Key Files Using Algo
1. **services.py**
   - Imports: `Algo.feed_algorithm.feed_engine.FeedAlgorithmEngine`
   - Imports: `Algo.feed_algorithm.services.FeedGenerationService`

2. **test_integration.py**
   - Contains integration tests for the algorithm

3. **tests.py**
   - Contains unit tests for feed algorithm components

## Configuration
```python
# settings.py
FEED_ALGORITHM_CONFIG = {
    'DEFAULT_FEED_SIZE': 20,
    'CACHE_TIMEOUT': 300  # 5 minutes
}
```

## Testing
- Comprehensive test suite in `Algo/tests/__init__.py`
- Tests cover:
  - Models
  - Feed engine
  - API endpoints
  - Scoring algorithms
  - Performance metrics

## Documentation
- `FEED_ALGORITHM_FRD.md`: Functional requirements
- `FEED_COMPOSITION_GUIDE.md`: Feed composition guidelines
- `feed_algorithm_integration.md`: Development log

## Playground
- Interactive testing environment
- Visual scoring breakdown
- Real-time feed generation testing

## Dependencies
- Django
- Graphene-Django
- django-graphql-jwt (for authentication)
- Custom algorithm from `Algo/feed_algorithm/`
