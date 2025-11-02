from rest_framework import serializers
from django.urls import reverse
from .models import *

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_main_university_store', 'created_at']

class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'description']

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            'source_type', 'name', 'code', 'department',
            'category', 'specifications', 'source_type',
            'university_master_item',
        ]
    
    category = serializers.StringRelatedField()


class InspectionCertificateSerializer(serializers.ModelSerializer):

    item_count = serializers.SerializerMethodField(method_name='get_item_count')
    items_link = serializers.SerializerMethodField(method_name='get_items_link')
    class Meta:
        model = InspectionCertificate
        fields = [
            'id', 'certificate_number', 'issued_on', 'issued_to',
            'contracter', 'indenter', 'consignee', 'department',
            'date_of_delivery', 'delivery_status', 'stock_register',
            'remarks', 'created_by', 'item_count', 'items_link'
        ]

    def get_item_count(self, obj):
        return InspectionItem.objects.filter(inspection=obj).count()
    
    def get_items_link(self, obj):
        request = self.context['request']
        url = reverse('certificate-items-list', kwargs={'certificate_pk': obj.id})
        return request.build_absolute_uri(url)


class UpdateInspectionCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionCertificate
        fields = ['remarks', 'delivery_status']


class ListInspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = [
            'id', 'tendered_quantity',
            'accepted_quantity', 'rejected_quantity', 'feed_back', 'item',
        ]
    
    item = ItemSerializer()

class InspectionItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        help_text='Link to an existing item',
    )

    class Meta:
        model = InspectionItem
        fields = [
            'id', 'tendered_quantity',
            'accepted_quantity', 'rejected_quantity', 'feed_back', 'item',
        ]

    def validate_item(self, value):
        certificate = InspectionCertificate.objects.get(pk=self.context['certificate_id'])
        if not Item.objects.filter(department=certificate.department, pk=value.id).exists():
            raise serializers.ValidationError('Item does not belong to specifies department')
        
        return value
    
    def create(self, validated_data):
        validated_data['inspection_id'] = self.context['certificate_id']
        return super().create(validated_data)
    
class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = [
            'id', 'batch_number', 'source_type' ,'inspection_item',
            'transfer_item', 'item', 'source_store', 'warranty_period_months',
            'warranty_expiry_date', 'expected_life_years', 'manufacture_date', 
            'expiry_date', 'batch_specifications', 'remarks', 'is_active', 'created_by',
            'total_quantity', 'current_quantity'
        ]
        read_only_fields = ['total_quantity', 'current_quantity']

class StockRegisterSerializer(serializers.ModelSerializer):
    indexes = serializers.SerializerMethodField(method_name='get_indexes')
    class Meta:
        model = StockRegister
        fields = [
            'id', 'register_name', 'register_number', 'register_type',
            'store', 'is_active', 'indexes'
        ]
    
    def get_indexes(self, obj):
        item_qs = StockEntry.objects.select_related('item').filter(
            stock_register=obj
        ).values('item__code', 'item__name').distinct()

        summary = []

        for item in item_qs:
            summary.append({
                'code': item['item__code'],
                'name': item['item__name']
            })
        
        entry_link = None
        if self.context['request']:
            entry_link = self.context['request'].build_absolute_uri(
                reverse('stockentry-list') + f'?stock_register={obj.id}'
            )

        return {
            'indexes': summary,
            'view_all_entries': entry_link
        }



    
        

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'code', 'store_type',
            'department', 'parent_store', 'location', 'incharge_name', 
            'incharge_contact', 'registers'
        ]
    registers = StockRegisterSerializer(many=True, read_only=True)
    


class SimpleBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['batch_number', 'source_type', 'item']

class ListStoreInventrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreInventory
        fields = ['id', 'batch', 'quantity_on_hand', 'quantity_allocated', 'quantity_qr_tagged']

    batch = SimpleBatchSerializer()

class StoreInventrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreInventory
        fields = ['id', 'batch', 'quantity_on_hand', 'quantity_allocated', 'quantity_qr_tagged']
    
    def create(self, validated_data):
        validated_data['store_id'] = self.context['store_id']
        return super().create(validated_data)
    
class StockEnteySerializer(serializers.ModelSerializer):
    balance = serializers.IntegerField(help_text='balance after this stockentry')
    class Meta:
        model = StockEntry
        fields = [
            'id', 'entry_type', 'entry_number', 'item',
            'item', 'quantity', 'from_store', 'to_store', 'from_inspection',
            'to_location', 'stock_register', 'transfer_note',
            'created_by', 'balance'
        ]

class AssetTagListSerializer(serializers.ModelSerializer):
    """Serializer for list view"""
    item_name = serializers.CharField(source='batch.item.name', read_only=True)
    item_code = serializers.CharField(source='batch.item.code', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    store_name = serializers.CharField(source='current_store.name', read_only=True)
    store_code = serializers.CharField(source='current_store.code', read_only=True)
    location_name = serializers.CharField(source='current_location.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    qr_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AssetTag
        fields = [
            'id', 'tag_number', 'qr_code_uuid', 'qr_image_url',
            'item_name', 'item_code', 'batch_number',
            'status', 'status_display',
            'store_name', 'store_code', 'location_name',
            'assigned_to', 'tagged_date', 'created_at'
        ]
    
    def get_qr_image_url(self, obj):
        if obj.qr_code_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code_image.url)
            return obj.qr_code_image.url
        return None



class AssetTagDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed view with all related data"""
    full_details = serializers.SerializerMethodField()
    qr_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AssetTag
        fields = [
            'id', 'tag_number', 'qr_code_uuid', 'qr_image_url',
            'batch', 'current_store', 'current_location',
            'status', 'assigned_to', 'tagged_date',
            'remarks', 'created_at', 'updated_at',
            'full_details'
        ]
        read_only_fields = ['tag_number', 'qr_code_uuid', 'tagged_date', 'created_at', 'updated_at']
    
    def get_full_details(self, obj):
        return obj.get_full_details()
    
    def get_qr_image_url(self, obj):
        if obj.qr_code_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code_image.url)
            return obj.qr_code_image.url
        return None


class AssetTagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assets"""
    
    class Meta:
        model = AssetTag
        fields = [
            'batch', 'current_store', 'current_location',
            'status', 'assigned_to', 'remarks', 'created_by'
        ]
    
    def create(self, validated_data):
        return AssetTag.objects.create(**validated_data)


class AssetTagUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating asset status/location"""
    
    class Meta:
        model = AssetTag
        fields = [
            'status', 'current_store', 'current_location',
            'assigned_to', 'remarks'
        ]

class GenerateQRTagsSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
        help_text='Number of QR tags to generate'
    )


