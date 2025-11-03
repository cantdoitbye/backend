# Shop Module - Completion Checklist & Action Plan

## Critical Bugs to Fix Immediately

### 1. Model Method Name Errors
**Priority: CRITICAL**

**Issue**: Python magic methods have incorrect naming
```python
# Current (WRONG)
def _str_(self):
    return self.name

# Should be
def __str__(self):
    return self.name
```

**Files to Fix**:
- `shop/models.py` - All model classes (Product, Rating, ReviewShop, ProductCategory, Order)

**Impact**: String representation of objects won't work properly

---

### 2. Order Model Save Method Bug
**Priority: CRITICAL**

**Issue**: Property name mismatch in Order.save()
```python
# Current (WRONG)
def save(self, *args, **kwargs):
    self.order_at = datetime.now()  # Property doesn't exist
    super().save(*args, **kwargs)

# Should be
def save(self, *args, **kwargs):
    self.order_date = datetime.now()
    super().save(*args, **kwargs)
```

**File**: `shop/models.py` - Order class

**Impact**: Order save operations will fail

---

### 3. Query Return Type Mismatch
**Priority: HIGH**

**Issue**: Wrong return type in query resolver
```python
# Current (WRONG) in shop/graphql/query.py
def resolve_my_product_order(self, info):
    # ...
    return [ReviewShopType.from_neomodel(x) for x in orders]

# Should be
def resolve_my_product_order(self, info):
    # ...
    return [OrderType.from_neomodel(x) for x in orders]
```

**File**: `shop/graphql/query.py` - resolve_my_product_order method

**Impact**: Query returns wrong data structure

---

### 4. ProductType Category Field Bug
**Priority: HIGH**

**Issue**: Wrong type used for category conversion
```python
# Current (WRONG) in shop/graphql/types.py
productcategory=UserType.from_neomodel(product.productcategory.single()) if product.productcategory.single() else None

# Should be
productcategory=ProductCategoryType.from_neomodel(product.productcategory.single()) if product.productcategory.single() else None
```

**File**: `shop/graphql/types.py` - ProductType.from_neomodel method

**Impact**: Product category data returns user data instead

---

### 5. Incomplete Order Model __str__ Method
**Priority: MEDIUM**

**Issue**: Method returns nothing
```python
# Current (WRONG)
def _str_(self):
    return

# Should be
def __str__(self):
    return f"Order {self.uid} - {self.quantity} items"
```

**File**: `shop/models.py` - Order class

---

## Security & Authorization Issues

### 6. Missing Ownership Validation
**Priority: CRITICAL**

**Issue**: Any authenticated user can update/delete any item by knowing the UID

**Required Changes**:

**Product Updates/Deletes**:
```python
@login_required
def mutate(self, info, input):
    try:
        product = Product.nodes.get(uid=input.uid)
        
        # ADD THIS CHECK
        user = info.context.user
        payload = info.context.payload
        user_id = payload.get('user_id')
        creator = product.created_by.single()
        
        if not creator or creator.user_id != user_id:
            raise GraphQLError("You don't have permission to modify this product")
        
        # ... rest of update logic
```

**Files to Update**:
- `shop/graphql/mutations.py`:
  - UpdateProduct
  - DeleteProduct
  - UpdateProductCategory
  - DeleteProductCategory

**Rating/Review/Order Updates**:
```python
# Check if user owns the rating/review/order
user_node = rating_instance.user.single()
if not user_node or user_node.user_id != user_id:
    raise GraphQLError("You don't have permission to modify this item")
```

**Files to Update**:
- `shop/graphql/mutations.py`:
  - UpdateRating
  - DeleteRating
  - UpdateReviewShop
  - DeleteReviewShop
  - UpdateOrder
  - DeleteOrder

---

### 7. Missing Input Validation
**Priority: HIGH**

**Required Validations**:

**Price Validation**:
```python
if input.price is not None and input.price < 0:
    raise GraphQLError("Price cannot be negative")
```

**Rating Validation**:
```python
if input.rating < 1 or input.rating > 5:
    raise GraphQLError("Rating must be between 1 and 5")
```

**Quantity Validation**:
```python
if input.quantity < 1:
    raise GraphQLError("Quantity must be at least 1")
```

**Files to Update**:
- `shop/graphql/mutations.py` - All mutation classes

---

## Missing Core Features

### 8. Pagination Support
**Priority: HIGH**

**What's Needed**:
```python
# Add to shop/graphql/input.py
class PaginationInput(graphene.InputObjectType):
    page = graphene.Int(default_value=1)
    page_size = graphene.Int(default_value=20)

# Update queries in shop/graphql/query.py
all_products = graphene.Field(
    ProductPaginatedType,
    pagination=PaginationInput()
)

def resolve_all_products(self, info, pagination=None):
    page = pagination.page if pagination else 1
    page_size = pagination.page_size if pagination else 20
    
    skip = (page - 1) * page_size
    products = Product.nodes.all()[skip:skip + page_size]
    total = len(Product.nodes.all())
    
    return ProductPaginatedType(
        items=[ProductType.from_neomodel(p) for p in products],
        total=total,
        page=page,
        page_size=page_size
    )
```

**Files to Create/Update**:
- `shop/graphql/input.py` - Add PaginationInput
- `shop/graphql/types.py` - Add paginated types
- `shop/graphql/query.py` - Update all list queries

---

### 9. Filtering & Sorting
**Priority: HIGH**

**What's Needed**:
```python
# Add to shop/graphql/input.py
class ProductFilterInput(graphene.InputObjectType):
    category_uid = graphene.String()
    min_price = graphene.Float()
    max_price = graphene.Float()
    search = graphene.String()
    
class ProductSortInput(graphene.InputObjectType):
    field = graphene.String()  # name, price, created_at
    order = graphene.String()  # asc, desc

# Update query
all_products = graphene.List(
    ProductType,
    filter=ProductFilterInput(),
    sort=ProductSortInput()
)
```

**Files to Update**:
- `shop/graphql/input.py` - Add filter/sort inputs
- `shop/graphql/query.py` - Implement filtering logic

---

### 10. Duplicate Rating/Review Prevention
**Priority: MEDIUM**

**What's Needed**:
```python
# In CreateRating mutation
existing_ratings = list(product_instance.rating.filter(user=user_instance))
if existing_ratings:
    raise GraphQLError("You have already rated this product. Use update instead.")

# In CreateReviewShop mutation
existing_reviews = list(product_instance.reviewshop.filter(user=user_instance))
if existing_reviews:
    raise GraphQLError("You have already reviewed this product. Use update instead.")
```

**Files to Update**:
- `shop/graphql/mutations.py` - CreateRating, CreateReviewShop

---

### 11. Average Rating Calculation
**Priority: MEDIUM**

**What's Needed**:
```python
# Add to ProductType in shop/graphql/types.py
class ProductType(ObjectType):
    # ... existing fields
    average_rating = graphene.Float()
    rating_count = graphene.Int()
    
    @classmethod
    def from_neomodel(cls, product):
        ratings = list(product.rating)
        avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
        
        return cls(
            # ... existing fields
            average_rating=avg_rating,
            rating_count=len(ratings),
        )
```

**Files to Update**:
- `shop/graphql/types.py` - ProductType

---

### 12. Order Status Management
**Priority: HIGH**

**What's Needed**:
```python
# Add to shop/models.py
class Order(DjangoNode, StructuredNode):
    # ... existing fields
    status = StringProperty(
        choices={
            'pending': 'Pending',
            'confirmed': 'Confirmed',
            'processing': 'Processing',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled'
        },
        default='pending'
    )
    total_price = FloatProperty()
    shipping_address = JSONProperty()
    payment_status = StringProperty(default='pending')
```

**Files to Update**:
- `shop/models.py` - Order model
- `shop/graphql/types.py` - OrderType
- `shop/graphql/input.py` - Order inputs
- `shop/graphql/mutations.py` - Order mutations

---

### 13. Inventory Management
**Priority: HIGH**

**What's Needed**:
```python
# Add to shop/models.py
class Product(DjangoNode, StructuredNode):
    # ... existing fields
    stock_quantity = IntegerProperty(default=0)
    is_available = BooleanProperty(default=True)
    low_stock_threshold = IntegerProperty(default=10)

# Add validation in CreateOrder
if product.stock_quantity < input.quantity:
    raise GraphQLError("Insufficient stock available")

# Update stock after order
product.stock_quantity -= input.quantity
if product.stock_quantity <= 0:
    product.is_available = False
product.save()
```

**Files to Update**:
- `shop/models.py` - Product model
- `shop/graphql/mutations.py` - CreateOrder, UpdateOrder

---

## Data Consistency Issues

### 14. Missing Relationship Connections
**Priority: HIGH**

**Issue**: Some relationships are not bidirectionally connected

**Fix in CreateRating**:
```python
# Current
rating_instance.user.connect(user_instance)
rating_instance.product.connect(product_instance)
product_instance.rating.connect()  # INCOMPLETE - missing argument

# Should be
rating_instance.user.connect(user_instance)
rating_instance.product.connect(product_instance)
product_instance.rating.connect(rating_instance)
```

**File**: `shop/graphql/mutations.py` - CreateRating

---

### 15. Soft Delete Consistency
**Priority: MEDIUM**

**Issue**: Inconsistent delete behavior (some soft, some hard)

**Recommendation**: Standardize to soft delete for all entities

**Files to Update**:
- `shop/graphql/mutations.py`:
  - DeleteRating - Change to soft delete
  - DeleteReviewShop - Change to soft delete
  - DeleteProductCategory - Change to soft delete

---

## Testing Requirements

### 16. Unit Tests
**Priority: HIGH**

**What's Needed**: Create `shop/tests.py` with:

```python
from django.test import TestCase
from neomodel import db
from .models import Product, Rating, ReviewShop, ProductCategory, Order
from auth_manager.models import Users

class ProductModelTests(TestCase):
    def setUp(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")  # Clean database
        
    def test_product_creation(self):
        # Test product creation
        pass
        
    def test_product_relationships(self):
        # Test relationships are created correctly
        pass

class ProductMutationTests(TestCase):
    def test_create_product_authenticated(self):
        # Test product creation with auth
        pass
        
    def test_create_product_unauthenticated(self):
        # Test product creation fails without auth
        pass
        
    def test_update_product_ownership(self):
        # Test only owner can update
        pass

class ProductQueryTests(TestCase):
    def test_get_all_products_superuser(self):
        # Test superuser can see all
        pass
        
    def test_get_my_products(self):
        # Test user sees only their products
        pass
```

**Test Coverage Needed**:
- Model creation and validation
- Relationship creation
- Authentication requirements
- Authorization checks
- Query filtering
- Mutation operations
- Error handling

---

### 17. Integration Tests
**Priority: MEDIUM**

**What's Needed**: Test complete workflows

```python
class OrderWorkflowTests(TestCase):
    def test_complete_order_flow(self):
        # 1. Create product
        # 2. Create rating
        # 3. Create review
        # 4. Create order
        # 5. Verify stock updated
        # 6. Verify relationships
        pass
```

---

## Performance Optimization

### 18. Query Optimization
**Priority: MEDIUM**

**What's Needed**:
- Add indexes on frequently queried fields
- Optimize relationship traversals
- Implement query result caching

```python
# Add to models
class Product(DjangoNode, StructuredNode):
    uid = UniqueIdProperty(index=True)
    name = StringProperty(index=True)
    price = FloatProperty(index=True)
    created_at = DateTimeProperty(index=True)
```

**Files to Update**:
- `shop/models.py` - Add index=True to key fields

---

### 19. N+1 Query Problem
**Priority: MEDIUM**

**Issue**: Multiple database queries when fetching related data

**Solution**: Implement data loaders or optimize queries

```python
# Consider using graphene-django's optimization
from graphene_django.filter import DjangoFilterConnectionField

# Or implement custom data loaders
from promise import Promise
from promise.dataloader import DataLoader
```

---

## Documentation & Developer Experience

### 20. API Documentation
**Priority: MEDIUM**

**What's Needed**:
- GraphQL schema documentation
- Example queries and mutations
- Error code documentation
- Rate limiting documentation

**Create**: `shop/docs/API_EXAMPLES.md`

---

### 21. Admin Interface
**Priority: LOW**

**What's Needed**: Populate `shop/admin.py`

```python
from django.contrib import admin
from django_neomodel import admin as neo_admin
from .models import Product, Rating, ReviewShop, ProductCategory, Order

# Register models for admin interface
# Note: Neo4j admin integration may be limited
```

---

## Additional Features

### 22. Product Images
**Priority: MEDIUM**

**What's Needed**:
```python
# Add to Product model
class Product(DjangoNode, StructuredNode):
    # ... existing fields
    images = ArrayProperty(StringProperty())  # Array of image URLs
    thumbnail = StringProperty()
```

**Integration**: Use existing `auth_manager.Utils.generate_presigned_url` for S3 uploads

---

### 23. Wishlist Feature
**Priority: LOW**

**What's Needed**:
```python
# Add to Users model in auth_manager
class Users(DjangoNode, StructuredNode):
    # ... existing fields
    wishlist = RelationshipTo('shop.models.Product', 'WISHLISTED')

# Create mutations
class AddToWishlist(graphene.Mutation):
    # Implementation
    pass

class RemoveFromWishlist(graphene.Mutation):
    # Implementation
    pass
```

---

### 24. Product Search
**Priority: MEDIUM**

**What's Needed**:
```python
# Add search query
search_products = graphene.List(
    ProductType,
    query=graphene.String(required=True)
)

def resolve_search_products(self, info, query):
    # Implement full-text search
    # Consider using Neo4j full-text indexes
    pass
```

---

### 25. Analytics & Reporting
**Priority: LOW**

**What's Needed**:
- Sales reports
- Popular products
- Revenue tracking
- User purchase history

```python
# Add analytics queries
class Query(graphene.ObjectType):
    product_analytics = graphene.Field(
        ProductAnalyticsType,
        product_uid=graphene.String(required=True)
    )
    
    sales_report = graphene.Field(
        SalesReportType,
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime()
    )
```

---

## Configuration & Deployment

### 26. Environment Configuration
**Priority: HIGH**

**What's Needed**: Document required environment variables

```bash
# .env
NEO4J_BOLT_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Shop module specific
SHOP_DEFAULT_CURRENCY=USD
SHOP_TAX_RATE=0.08
SHOP_ENABLE_INVENTORY=true
```

---

### 27. Database Indexes
**Priority: HIGH**

**What's Needed**: Create Neo4j indexes

```cypher
-- Run these in Neo4j
CREATE INDEX product_uid IF NOT EXISTS FOR (p:Product) ON (p.uid);
CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name);
CREATE INDEX product_price IF NOT EXISTS FOR (p:Product) ON (p.price);
CREATE INDEX order_date IF NOT EXISTS FOR (o:Order) ON (o.order_date);
CREATE INDEX category_name IF NOT EXISTS FOR (c:ProductCategory) ON (c.name);
```

**Create**: `shop/db/indexes.cypher`

---

### 28. Migration Strategy
**Priority: MEDIUM**

**What's Needed**: Document data migration approach

Since Neo4j doesn't use traditional migrations:
- Document schema changes
- Create Cypher scripts for data transformations
- Version control schema definitions

---

## Monitoring & Logging

### 29. Error Logging
**Priority: HIGH**

**What's Needed**: Improve error handling and logging

```python
import logging

logger = logging.getLogger(__name__)

@login_required
def mutate(self, info, input):
    try:
        # ... operation
    except Product.DoesNotExist:
        logger.warning(f"Product not found: {input.uid}")
        return UpdateProduct(product=None, success=False, message="Product not found")
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}", exc_info=True)
        return UpdateProduct(product=None, success=False, message="An error occurred")
```

**Files to Update**: All mutation files

---

### 30. Performance Monitoring
**Priority: MEDIUM**

**What's Needed**:
- Query performance tracking
- Slow query logging
- Relationship traversal metrics

---

## Summary: Priority Action Plan

### Phase 1: Critical Fixes (Week 1)
1. ✅ Fix all `_str_` → `__str__` naming issues
2. ✅ Fix Order.save() method bug
3. ✅ Fix query return type mismatch
4. ✅ Fix ProductType category field bug
5. ✅ Add ownership validation to all mutations
6. ✅ Add input validation (price, rating, quantity)
7. ✅ Fix missing relationship connection in CreateRating

### Phase 2: Core Features (Week 2-3)
8. ✅ Implement pagination
9. ✅ Add filtering and sorting
10. ✅ Implement order status management
11. ✅ Add inventory management
12. ✅ Prevent duplicate ratings/reviews
13. ✅ Add average rating calculation

### Phase 3: Testing & Quality (Week 4)
14. ✅ Write unit tests
15. ✅ Write integration tests
16. ✅ Add comprehensive error logging
17. ✅ Create API documentation with examples

### Phase 4: Optimization (Week 5)
18. ✅ Add database indexes
19. ✅ Optimize queries
20. ✅ Implement caching strategy
21. ✅ Performance monitoring

### Phase 5: Enhancement (Week 6+)
22. ✅ Add product images
23. ✅ Implement search functionality
24. ✅ Add wishlist feature
25. ✅ Build analytics and reporting
26. ✅ Admin interface

---

## Estimated Effort

| Phase | Tasks | Estimated Time | Priority |
|-------|-------|----------------|----------|
| Phase 1 | 7 critical fixes | 1 week | CRITICAL |
| Phase 2 | 6 core features | 2 weeks | HIGH |
| Phase 3 | 4 testing tasks | 1 week | HIGH |
| Phase 4 | 4 optimization tasks | 1 week | MEDIUM |
| Phase 5 | 5 enhancements | 2+ weeks | LOW |

**Total Estimated Time**: 7-8 weeks for full completion

---

## Success Criteria

The shop module will be considered complete when:

- ✅ All critical bugs are fixed
- ✅ All mutations have proper authorization
- ✅ Input validation is comprehensive
- ✅ Test coverage > 80%
- ✅ Pagination and filtering work on all list queries
- ✅ Order workflow is complete (status, inventory, payment)
- ✅ Performance is optimized (indexed, cached)
- ✅ Documentation is complete
- ✅ Production-ready error handling and logging
- ✅ Security audit passed

---

## Next Steps

1. **Immediate**: Fix all Phase 1 critical bugs
2. **Review**: Get code review on fixes
3. **Test**: Write tests for fixed functionality
4. **Plan**: Schedule Phase 2 features with product team
5. **Document**: Keep this checklist updated as work progresses
