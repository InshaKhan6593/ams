from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    DepartmentViewSet,
    LocationViewSet,
    ItemCategoryViewSet,
    ItemViewSet,
    StoreViewSet,
    StockRegisterViewSet,
    InspectionCertificateViewSet,
    InspectionItemViewSet,
    BatchViewSet,
    StoreInventoryViewSet,
    StockEntryViewSet,
    TransferNoteViewSet,
    TransferNoteItemViewSet,
    RequisitionViewSet
)

# ============================================================================
# MAIN ROUTER
# ============================================================================

router = DefaultRouter()

# Register main viewsets
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'item-categories', ItemCategoryViewSet, basename='itemcategory')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'stock-registers', StockRegisterViewSet, basename='stockregister')
router.register(r'inspection-certificates', InspectionCertificateViewSet, basename='inspectioncertificate')
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'store-inventory', StoreInventoryViewSet, basename='storeinventory')
router.register(r'stock-entries', StockEntryViewSet, basename='stockentry')
router.register(r'transfer-notes', TransferNoteViewSet, basename='transfernote')
router.register(r'requisitions', RequisitionViewSet, basename='requisition')
# ============================================================================
# NESTED ROUTERS
# ============================================================================

# Department nested routes
department_router = routers.NestedSimpleRouter(router, r'departments', lookup='department')
department_router.register(r'stores', StoreViewSet, basename='department-stores')
department_router.register(r'items', ItemViewSet, basename='department-items')
department_router.register(r'locations', LocationViewSet, basename='department-locations')

# Store nested routes
store_router = routers.NestedSimpleRouter(router, r'stores', lookup='store')
store_router.register(r'inventory', StoreInventoryViewSet, basename='store-inventory')
store_router.register(r'registers', StockRegisterViewSet, basename='store-registers')
store_router.register(r'batches', BatchViewSet, basename='store-batches')

# Stock Register nested routes
register_router = routers.NestedSimpleRouter(router, r'stock-registers', lookup='register')
register_router.register(r'entries', StockEntryViewSet, basename='register-entries')

# Inspection Certificate nested routes
inspection_router = routers.NestedSimpleRouter(
    router, 
    r'inspection-certificates', 
    lookup='inspection'
)
inspection_router.register(r'items', InspectionItemViewSet, basename='inspection-items')

# Item nested routes
item_router = routers.NestedSimpleRouter(router, r'items', lookup='item')
item_router.register(r'batches', BatchViewSet, basename='item-batches')
item_router.register(r'stock-entries', StockEntryViewSet, basename='item-entries')

# Batch nested routes
batch_router = routers.NestedSimpleRouter(router, r'batches', lookup='batch')
batch_router.register(r'inventory', StoreInventoryViewSet, basename='batch-inventory')

# Item Category nested routes
category_router = routers.NestedSimpleRouter(router, r'item-categories', lookup='category')
category_router.register(r'items', ItemViewSet, basename='category-items')

# Transfer Note nested routes
transfer_note_router = routers.NestedSimpleRouter(router, r'transfer-notes', lookup='transfernote')
transfer_note_router.register(r'items', TransferNoteItemViewSet, basename='transfernote-items')

# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    path('', include(router.urls)),
    path('', include(department_router.urls)),
    path('', include(store_router.urls)),
    path('', include(register_router.urls)),
    path('', include(inspection_router.urls)),
    path('', include(item_router.urls)),
    path('', include(batch_router.urls)),
    path('', include(category_router.urls)),
    path('', include(transfer_note_router.urls)),
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS DOCUMENTATION
# ============================================================================

"""
MAIN ENDPOINTS:
===============

Departments:
- GET     /api/departments/
- POST    /api/departments/
- GET     /api/departments/{id}/
- PUT     /api/departments/{id}/
- PATCH   /api/departments/{id}/
- DELETE  /api/departments/{id}/
- GET     /api/departments/{id}/stores/
- GET     /api/departments/{id}/items/
- GET     /api/departments/{id}/locations/

Locations:
- GET     /api/locations/
- POST    /api/locations/
- GET     /api/locations/{id}/
- PUT     /api/locations/{id}/
- PATCH   /api/locations/{id}/
- DELETE  /api/locations/{id}/

Item Categories:
- GET     /api/item-categories/
- POST    /api/item-categories/
- GET     /api/item-categories/{id}/
- PUT     /api/item-categories/{id}/
- PATCH   /api/item-categories/{id}/
- DELETE  /api/item-categories/{id}/
- GET     /api/item-categories/{id}/items/

Items:
- GET     /api/items/
- POST    /api/items/
- GET     /api/items/{id}/
- PUT     /api/items/{id}/
- PATCH   /api/items/{id}/
- DELETE  /api/items/{id}/
- GET     /api/items/{id}/batches/
- GET     /api/items/{id}/inventory/
- GET     /api/items/{id}/stock-entries/

Stores:
- GET     /api/stores/
- POST    /api/stores/
- GET     /api/stores/{id}/
- PUT     /api/stores/{id}/
- PATCH   /api/stores/{id}/
- DELETE  /api/stores/{id}/
- GET     /api/stores/{id}/inventory/
- GET     /api/stores/{id}/registers/
- GET     /api/stores/{id}/batches/

Stock Registers:
- GET     /api/stock-registers/
- POST    /api/stock-registers/
- GET     /api/stock-registers/{id}/
- PUT     /api/stock-registers/{id}/
- PATCH   /api/stock-registers/{id}/
- DELETE  /api/stock-registers/{id}/
- GET     /api/stock-registers/{id}/entries/
- GET     /api/stock-registers/{id}/summary/

Inspection Certificates:
- GET     /api/inspection-certificates/
- POST    /api/inspection-certificates/
- GET     /api/inspection-certificates/{id}/
- PUT     /api/inspection-certificates/{id}/
- PATCH   /api/inspection-certificates/{id}/
- DELETE  /api/inspection-certificates/{id}/
- POST    /api/inspection-certificates/{id}/add_item/
- GET     /api/inspection-certificates/{id}/batches/
- POST    /api/inspection-certificates/{id}/process/

Batches:
- GET     /api/batches/
- POST    /api/batches/
- GET     /api/batches/{id}/
- PUT     /api/batches/{id}/
- PATCH   /api/batches/{id}/
- DELETE  /api/batches/{id}/
- GET     /api/batches/{id}/inventory/
- GET     /api/batches/{id}/transfers/

Store Inventory:
- GET     /api/store-inventory/
- GET     /api/store-inventory/{id}/
- GET     /api/store-inventory/by_store/?store_id={id}
- GET     /api/store-inventory/by_batch/?batch_id={id}
- GET     /api/store-inventory/low_stock/

Stock Entries:
- GET     /api/stock-entries/
- POST    /api/stock-entries/
- GET     /api/stock-entries/{id}/
- GET     /api/stock-entries/by_store/?store_id={id}
- GET     /api/stock-entries/by_item/?item_id={id}
- GET     /api/stock-entries/by_batch/?batch_id={id}
- POST    /api/stock-entries/adjustment/
- POST    /api/stock-entries/{id}/reverse/


NESTED ENDPOINTS:
=================

Department Nested:
- GET     /api/departments/{dept_id}/stores/
- GET     /api/departments/{dept_id}/items/
- GET     /api/departments/{dept_id}/locations/

Store Nested:
- GET     /api/stores/{store_id}/inventory/
- GET     /api/stores/{store_id}/registers/
- GET     /api/stores/{store_id}/batches/

Stock Register Nested:
- GET     /api/stock-registers/{register_id}/entries/

Inspection Certificate Nested:
- GET     /api/inspection-certificates/{inspection_id}/items/
- POST    /api/inspection-certificates/{inspection_id}/items/
- GET     /api/inspection-certificates/{inspection_id}/items/{item_id}/
- PUT     /api/inspection-certificates/{inspection_id}/items/{item_id}/
- PATCH   /api/inspection-certificates/{inspection_id}/items/{item_id}/
- DELETE  /api/inspection-certificates/{inspection_id}/items/{item_id}/

Item Nested:
- GET     /api/items/{item_id}/batches/
- GET     /api/items/{item_id}/stock-entries/

Batch Nested:
- GET     /api/batches/{batch_id}/inventory/

Category Nested:
- GET     /api/item-categories/{category_id}/items/


QUERY PARAMETERS:
=================

Pagination:
?page=1&page_size=20

Filtering:
?department=1&store_type=MAIN&is_active=true

Search:
?search=keyword

Ordering:
?ordering=-created_at  (descending)
?ordering=name         (ascending)

Combined:
?department=1&search=laptop&ordering=-created_at&page=1
"""