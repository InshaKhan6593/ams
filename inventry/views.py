from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv

class DepartmentViewSet(ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class ItemCategoryViewSet(ModelViewSet):
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer

class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class InspectionCertificateViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'options', 'header']
    queryset = InspectionCertificate.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateInspectionCertificateSerializer
        return InspectionCertificateSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}

class InspectionItemViewSet(ModelViewSet):
    
    def get_queryset(self):
        return InspectionItem.objects.filter(inspection_id=self.kwargs['certificate_pk'])
    
    def get_serializer_context(self):
        return {'certificate_id': self.kwargs['certificate_pk']}
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ListInspectionItemSerializer
        return InspectionItemSerializer
    
class BatchViewSet(ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

class StoreViewSet(ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class StoreInventryViewSet(ModelViewSet):
    
    def get_queryset(self):
        return StoreInventory.objects.filter(store=self.kwargs['store_pk'])
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ListStoreInventrySerializer
        return StoreInventrySerializer

    def get_serializer_context(self):
        return {'store_id': self.kwargs['store_pk']}
    
class StockEntryViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['stock_register']
    queryset = StockEntry.objects.all()
    serializer_class = StockEnteySerializer

class StockRegisterViewSet(ModelViewSet):
    queryset = StockRegister.objects.select_related('store').all()
    serializer_class = StockRegisterSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    


    
