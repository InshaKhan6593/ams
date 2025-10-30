from django.contrib import admin
from django.urls import path

from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('inspections', views.InspectionViewSet)
router.register('stockentries', views.StockEntryViewSet)
router.register('storeinventry', views.StoreInventryViewSet)

inspection_router = routers.NestedDefaultRouter(router, 'inspections', lookup='inspection')
inspection_router.register('items', views.InspectionItemViewSet, basename='inspection-items')


urlpatterns = router.urls + inspection_router.urls