from django.contrib import admin
from django.urls import path

from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('departments', views.DepartmentViewSet)
router.register('item-categories', views.ItemCategoryViewSet)
router.register('items', views.ItemViewSet)
router.register('certificates', views.InspectionCertificateViewSet)
router.register('batches', views.BatchViewSet)
router.register('stores', views.StoreViewSet)
router.register('stock-entries', views.StockEntryViewSet)
router.register('stock-registers', views.StockRegisterViewSet)
router.register('asset-tags', views.AssetTagViewSet, basename='asset-tags')


certificates_router = routers.NestedDefaultRouter(
    router,
    'certificates',
    lookup='certificate'
)
certificates_router.register('items', views.InspectionItemViewSet, basename='certificate-items')

stores_router = routers.NestedDefaultRouter(router, 'stores', lookup='store')
stores_router.register('inventries', views.StoreInventryViewSet, basename='store-inventries')

urlpatterns = router.urls + certificates_router.urls + stores_router.urls