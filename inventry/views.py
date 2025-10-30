from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.decorators import action

class InspectionViewSet(ModelViewSet):
    queryset = InspectionCertificate.objects.prefetch_related('items').all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ListInspectionCertificateSerializer
        return InspectionCertificateSerializer

class InspectionItemViewSet(ModelViewSet):
    
    def get_queryset(self):
        return InspectionItem.objects.prefetch_related('inspection').filter(inspection_id=self.kwargs['inspection_pk'])
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LisInspectionItemSerializer
        return InspectionItemSerializer
    
    def get_serializer_context(self):
        return {'inspection_id': self.kwargs['inspection_pk']}


class StockEntryViewSet(ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer

class StoreInventryViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet
):
    queryset = StoreInventory.objects.all()
    serializer_class = StoreInventrySerializer

