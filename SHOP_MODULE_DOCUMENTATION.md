# Shop Module - Complete Documentation

## Overview

The Shop module is a comprehensive e-commerce system built on Django with Neo4j graph database (using neomodel) and GraphQL API. It enables users to create products, manage product categories, handle orders, and collect ratings and reviews.

## Architecture

### Technology Stack
- **Framework**: Django
- **Database**: Neo4j (Graph Database)
- **ORM**: neomodel + django-neomodel
- **API**: GraphQL (using graphene-django)
- **Authentication**: JWT (graphql-jwt)

### Module Structure
```
shop/
├── models.py                    # Neo4j graph models
├── apps.py                      # Django app configuration
├── admin.py                     # Django admin (empty)
├── views.py                     # Django views (empty)
├── __init__.py
└── graphql/
    ├── schema.py                # GraphQL schema definition
    ├── types.py                 # GraphQL type definitions
    ├── mutations.py             # GraphQL mutations (CRUD operations)
    ├── query.py                 # GraphQL queries
    ├── input.py                 # GraphQL input types
    └── messages.py              # User-facing messages
```

## Data Models

### 1. Product
The core entity representing items for sale.

**Properties:**
- `uid`: UniqueIdProperty - Auto-generated unique identifier
- `name`: StringProperty - Product name
- `description`: StringProperty - Product description
- `cta_link`: StringProperty - Call-to-action link
- `cta`: StringProperty - Call-to-action text
- `hashtags`: StringProperty - Product hashtags
- `highlights`: JSONProperty - Product highlights (structured data)
- `price`: FloatProperty (default: 2.0) - Product price
- `created_at`: DateTimeProperty - Creation timestamp
- `updated_at`: DateTimeProperty - Last update timestamp
- `is_deleted`: BooleanProperty (default: False) - Soft delete flag

**Relationships:**
- `created_by` → Users (CREATED_BY)
- `productcategory` → ProductCategory (HAS_PRODUCT_CATEGORY)
- `rating` → Rating (HAS_RATING)
- `reviewshop` → ReviewShop (HAS_REVIEW)
- `order` → Order (HAS_ORDER)

### 2. Rating
User ratings for products (numeric scores).

**Properties:**
- `uid`: UniqueIdProperty
- `rating`: IntegerProperty - Numeric rating value

**Relationships:**
- `user` → Users (RATED_BY)
- `product` → Product (HAS_PRODUCT)

### 3. ReviewShop
Text-based reviews for products.

**Properties:**
- `uid`: UniqueIdProperty
- `text`: StringProperty - Review text content
- `created_at`: DateTimeProperty
- `updated_at`: DateTimeProperty
- `is_deleted`: BooleanProperty (default: False)

**Relationships:**
- `user` → Users (REVIEWED_BY)
- `product` → Product (HAS_PRODUCT)

### 4. ProductCategory
Categories for organizing products.

**Properties:**
- `uid`: UniqueIdProperty
- `name`: StringProperty - Category name
- `description`: StringProperty - Category description
- `created_at`: DateTimeProperty
- `updated_at`: DateTimeProperty
- `is_deleted`: BooleanProperty (default: False)

**Relationships:**
- `created_by` → Users (CREATED_BY)

### 5. Order
Customer orders for products.

**Properties:**
- `uid`: UniqueIdProperty
- `quantity`: IntegerProperty - Number of items ordered
- `order_date`: DateTimeProperty - Order timestamp
- `is_deleted`: BooleanProperty (default: False)

**Relationships:**
- `user` → Users (ORDERED_BY)
- `product` → Product (HAS_PRODUCT)

## GraphQL API

### Type System

#### ProductType
Full product information including all relationships.

**Fields:**
- All product properties
- `created_by`: UserType
- `productcategory`: ProductCategoryType
- `rating`: List[RatingNonProductType]
- `reviewshop`: List[ReviewShopNonProductType]
- `order`: List[OrderNonProductType]

#### RatingType / RatingNonProductType
- Full: Includes user and product
- NonProduct: Excludes product (prevents circular references)

#### ReviewShopType / ReviewShopNonProductType
- Full: Includes user and product
- NonProduct: Excludes product (prevents circular references)

#### OrderType / OrderNonProductType
- Full: Includes user and product
- NonProduct: Excludes product (prevents circular references)

#### ProductCategoryType
Category information with creator details.

### Queries

#### Product Queries
```graphql
# Get single product by UID
productByUid(uid: String!): ProductType

# Get all products (superuser only)
allProducts: [ProductType]

# Get current user's products
myProduct: [ProductType]
```

#### Rating Queries
```graphql
# Get single rating by UID
ratingByUid(uid: String!): RatingType

# Get all ratings (superuser only)
allRatings: [RatingType]

# Get ratings for current user's products
myProductRating: [RatingType]
```

#### Review Queries
```graphql
# Get single review by UID
reviewShopByUid(uid: String!): ReviewShopType

# Get all reviews (superuser only)
allReviewShops: [ReviewShopType]

# Get reviews for current user's products
myProductReview: [ReviewShopType]
```

#### Category Queries
```graphql
# Get single category by UID
productCategoryByUid(uid: String!): ProductCategoryType

# Get all categories (superuser only)
allProductCategories: [ProductCategoryType]
```

#### Order Queries
```graphql
# Get single order by UID
orderByUid(uid: String!): OrderType

# Get all orders (superuser only)
allOrders: [OrderType]

# Get orders for current user's products
myProductOrder: [OrderType]
```

### Mutations

#### Product Mutations

**Create Product**
```graphql
createProduct(input: CreateProductInput!): CreateProductPayload

input CreateProductInput {
  productCategoryUid: String
  name: String!
  description: String
  ctaLink: String
  cta: String
  hashtags: String
  highlights: JSONString
  price: Float!
}
```
- Requires authentication
- Automatically connects to authenticated user as creator
- Links to specified product category

**Update Product**
```graphql
updateProduct(input: UpdateProductInput!): UpdateProductPayload

input UpdateProductInput {
  uid: String!
  name: String
  description: String
  ctaLink: String
  cta: String
  hashtags: String
  highlights: JSONString
  price: Float
  isDeleted: Boolean
}
```
- Requires authentication
- All fields except `uid` are optional
- Updates `updated_at` timestamp automatically

**Delete Product**
```graphql
deleteProduct(input: DeleteProductInput!): DeleteProductPayload

input DeleteProductInput {
  uid: String!
}
```
- Soft delete (sets `is_deleted = True`)
- Requires authentication

#### Rating Mutations

**Create Rating**
```graphql
createRating(input: CreateRatingInput!): CreateRatingPayload

input CreateRatingInput {
  productUid: String!
  rating: Int!
}
```
- Requires authentication
- Automatically links to authenticated user
- Connects rating to product

**Update Rating**
```graphql
updateRating(input: UpdateRatingInput!): UpdateRatingPayload

input UpdateRatingInput {
  uid: String!
  rating: Int!
}
```

**Delete Rating**
```graphql
deleteRating(input: DeleteRatingInput!): DeleteRatingPayload

input DeleteRatingInput {
  uid: String!
}
```
- Hard delete (permanently removes from database)

#### Review Mutations

**Create Review**
```graphql
createReviewShop(input: CreateReviewShopInput!): CreateReviewShopPayload

input CreateReviewShopInput {
  productUid: String!
  text: String!
}
```
- Requires authentication
- Links review to user and product

**Update Review**
```graphql
updateReviewShop(input: UpdateReviewShopInput!): UpdateReviewShopPayload

input UpdateReviewShopInput {
  uid: String!
  text: String
  isDeleted: Boolean
}
```

**Delete Review**
```graphql
deleteReviewShop(input: DeleteReviewShopInput!): DeleteReviewShopPayload

input DeleteReviewShopInput {
  uid: String!
}
```
- Hard delete

#### Category Mutations

**Create Category**
```graphql
createProductCategory(input: CreateProductCategoryInput!): CreateProductCategoryPayload

input CreateProductCategoryInput {
  name: String!
  description: String
}
```
- Requires authentication
- Links to authenticated user as creator

**Update Category**
```graphql
updateProductCategory(input: UpdateProductCategoryInput!): UpdateProductCategoryPayload

input UpdateProductCategoryInput {
  uid: String!
  name: String
  description: String
  isDeleted: Boolean
}
```

**Delete Category**
```graphql
deleteProductCategory(input: DeleteProductCategoryInput!): DeleteProductCategoryPayload

input DeleteProductCategoryInput {
  uid: String!
}
```
- Hard delete

#### Order Mutations

**Create Order**
```graphql
createOrder(input: CreateOrderInput!): CreateOrderPayload

input CreateOrderInput {
  productUid: String!
  quantity: Int!
}
```
- Requires authentication
- Links order to user and product
- Sets order_date automatically

**Update Order**
```graphql
updateOrder(input: UpdateOrderInput!): UpdateOrderPayload

input UpdateOrderInput {
  uid: String!
  quantity: Int
  isDeleted: Boolean
}
```

**Delete Order**
```graphql
deleteOrder(input: DeleteOrderInput!): DeleteOrderPayload

input DeleteOrderInput {
  uid: String!
}
```
- Soft delete

## Integration Points

### 1. Authentication Integration
- **Module**: `auth_manager`
- **Integration**: All mutations require JWT authentication via `@login_required` decorator
- **User Relationship**: Users model has `product` relationship to Product model
- **User Context**: Authenticated user is extracted from JWT payload (`info.context.payload`)

### 2. Main Schema Integration
- **File**: `schema/schema.py`
- **Query Integration**: `ShopQuery` is mixed into main `Query` class
- **Mutation Integration**: `ShopMutation` is mixed into main `Mutation` class
- **Endpoint**: All shop operations available through main GraphQL endpoint

### 3. Django Settings
- **Registered App**: `'shop'` in `INSTALLED_APPS` (settings.py)
- **Database**: Uses Neo4j via neomodel configuration

## Authorization Model

### Permission Levels

1. **Public Access**: None (all operations require authentication)

2. **Authenticated Users**:
   - Create products, ratings, reviews, orders, categories
   - Update/delete their own content
   - View specific items by UID
   - View their own products and related data

3. **Superusers** (`@superuser_required`):
   - View all products
   - View all ratings
   - View all reviews
   - View all categories
   - View all orders

## Data Flow Examples

### Creating a Product
1. User authenticates and receives JWT token
2. User sends `createProduct` mutation with product details and category UID
3. System validates authentication
4. System retrieves user from JWT payload
5. System retrieves category by UID
6. System creates Product node
7. System creates relationships:
   - Product → User (CREATED_BY)
   - Product → Category (HAS_PRODUCT_CATEGORY)
   - User → Product (HAS_PRODUCT)
8. Returns ProductType with success message

### Creating a Rating
1. Authenticated user sends `createRating` mutation
2. System retrieves user from JWT
3. System retrieves product by UID
4. System creates Rating node
5. System creates relationships:
   - Rating → User (RATED_BY)
   - Rating → Product (HAS_PRODUCT)
6. Returns RatingType with success message

### Querying User's Products
1. User sends `myProduct` query
2. System extracts user_id from JWT payload
3. System retrieves User node
4. System traverses `product` relationship
5. Returns list of ProductType objects with all nested data

## Error Handling

### Common Error Scenarios
- **Authentication Failure**: "Authentication Failure" when user is anonymous
- **Not Found**: Returns `None` for single item queries when UID doesn't exist
- **General Errors**: Caught exceptions return error message in response

### Response Format
All mutations return:
```graphql
{
  success: Boolean!
  message: String!
  [entity]: [EntityType]  # null on failure
}
```

## Messages

User-facing messages are internationalized using Django's translation system:
- Product: Created, Updated, Deleted
- Rating: Created, Updated, Deleted
- Review: Created, Updated, Deleted
- Category: Created, Updated, Deleted
- Order: Created, Updated, Deleted

## Graph Database Relationships

### Relationship Diagram
```
User ──CREATED_BY──> Product
User ──HAS_PRODUCT──> Product
User ──RATED_BY────> Rating
User ──REVIEWED_BY─> ReviewShop
User ──ORDERED_BY──> Order
User ──CREATED_BY──> ProductCategory

Product ──HAS_PRODUCT_CATEGORY──> ProductCategory
Product ──HAS_RATING──> Rating
Product ──HAS_REVIEW──> ReviewShop
Product ──HAS_ORDER──> Order

Rating ──HAS_PRODUCT──> Product
ReviewShop ──HAS_PRODUCT──> Product
Order ──HAS_PRODUCT──> Product
```

## Best Practices & Patterns

### 1. Soft Delete Pattern
- Products, Reviews, Categories, and Orders use soft delete (`is_deleted` flag)
- Ratings use hard delete
- Queries filter out soft-deleted items

### 2. Timestamp Management
- `created_at`: Set automatically on creation
- `updated_at`: Updated automatically via `save()` method override

### 3. Circular Reference Prevention
- "NonProduct" types (RatingNonProductType, etc.) prevent circular references in GraphQL schema
- Used when product contains lists of related entities

### 4. Authentication Pattern
- JWT token in request headers
- User extracted from `info.context.payload`
- Consistent use of `@login_required` decorator

### 5. Error Handling Pattern
```python
try:
    # Operation logic
    return Success(entity=..., success=True, message=...)
except Exception as e:
    return Success(entity=None, success=False, message=str(e))
```

## Known Issues & Limitations

### 1. Model Issues
- `Order.save()` method references `self.order_at` but property is `order_date`
- `Product._str_()` method has incorrect name (should be `__str__`)
- Similar naming issues in other models

### 2. Query Issues
- `resolve_my_product_order` returns `ReviewShopType` instead of `OrderType`

### 3. Missing Features
- No pagination on list queries
- No filtering or sorting options
- No bulk operations
- No order status tracking
- No payment integration
- No inventory management

### 4. Security Considerations
- No ownership validation on updates/deletes
- Superuser can see all data but regular users can modify any item by UID
- No rate limiting on mutations

## Future Enhancements

### Recommended Improvements
1. **Add ownership validation** - Users should only update/delete their own content
2. **Implement pagination** - For all list queries
3. **Add filtering** - By category, price range, rating, etc.
4. **Order management** - Status tracking (pending, shipped, delivered, cancelled)
5. **Inventory system** - Stock tracking and availability
6. **Payment integration** - Payment processing and transaction records
7. **Search functionality** - Full-text search on products
8. **Analytics** - Sales reports, popular products, revenue tracking
9. **Image support** - Product images and galleries
10. **Wishlist feature** - Users can save products for later

## Testing

Currently, no test files exist for the shop module. Recommended test coverage:
- Model creation and relationships
- GraphQL query resolution
- Mutation operations (CRUD)
- Authentication and authorization
- Error handling
- Edge cases (missing data, invalid UIDs, etc.)

## Dependencies

### Python Packages
- `django` - Web framework
- `neomodel` - Neo4j ORM
- `django-neomodel` - Django integration for neomodel
- `graphene-django` - GraphQL integration
- `graphql-jwt` - JWT authentication

### External Services
- Neo4j database instance

### Internal Dependencies
- `auth_manager.models.Users` - User model
- `auth_manager.graphql.types.UserType` - User GraphQL type

## Deployment Considerations

1. **Database**: Ensure Neo4j is properly configured and accessible
2. **Environment Variables**: Configure database connection settings
3. **Migrations**: Neo4j doesn't use traditional migrations; schema is defined in models
4. **Indexes**: Consider adding indexes on frequently queried properties (uid, name, etc.)
5. **Monitoring**: Track query performance and relationship traversal costs

## Conclusion

The Shop module provides a solid foundation for e-commerce functionality with a graph database backend. The GraphQL API offers flexible querying capabilities, and the relationship-based data model enables complex queries across products, users, ratings, reviews, and orders. However, several improvements are needed for production readiness, particularly around authorization, pagination, and order management.
