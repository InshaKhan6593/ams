from rest_framework import serializers
from .models import (
    InspectionCertificate,
    InspectionItem,
    Department,
    ItemCategory,
    StockEntry,
    StoreInventory,
    Item
)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class ItemSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class InspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = '__all__'
        read_only_fields = ['inspection']
    
    def create(self, validated_data):
        validated_data['inspection_id'] = self.context['inspection_id']
        return super().create(validated_data)
    


class InspectionCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionCertificate
        fields = '__all__'

class ListInspectionCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionCertificate
        fields = '__all__'
    
    items = InspectionItemSerializer(many=True)

class LisInspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = '__all__'

    item = ItemSerilaizer()


class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = '__all__'

class StoreInventrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreInventory
        fields = '__all__'
