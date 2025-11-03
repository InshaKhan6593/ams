# serializers.py

from rest_framework import serializers
from .models import *
from rest_framework.reverse import reverse
# ============================================================================
# DEPARTMENT SERIALIZERS
# ============================================================================

class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing departments"""
    stores_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_main_university_store', 
                  'stores_count', 'items_count', 'created_at']
        read_only_fields = ['id', 'code', 'created_at']
    
    def get_stores_count(self, obj):
        return obj.store_set.count()
    
    def get_items_count(self, obj):
        return obj.items.count()


class DepartmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with nested relations"""
    stores_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    locations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_main_university_store', 
                  'stores_count', 'items_count', 'locations_count', 'created_at']
        read_only_fields = ['id', 'code', 'created_at']
    
    def get_stores_count(self, obj):
        return obj.store_set.count()
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_locations_count(self, obj):
        return obj.locations.count()


class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating departments"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_main_university_store']
        read_only_fields = ['id', 'code']


# ============================================================================
# LOCATION SERIALIZERS
# ============================================================================

class LocationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing locations"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'location_type', 'location_type_display',
                  'department', 'department_name', 'details']
        read_only_fields = ['id']


class LocationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for location"""
    department = DepartmentListSerializer(read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    
    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'location_type', 'location_type_display',
                  'department', 'details']
        read_only_fields = ['id']


class LocationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating locations"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'location_type', 'department', 'details']
        read_only_fields = ['id']


# ============================================================================
# ITEM CATEGORY SERIALIZERS
# ============================================================================

class ItemCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing categories"""
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'description', 'items_count']
        read_only_fields = ['id']
    
    def get_items_count(self, obj):
        return obj.item_set.count()


class ItemCategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for category"""
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'description', 'items_count']
        read_only_fields = ['id']
    
    def get_items_count(self, obj):
        return obj.item_set.count()


class ItemCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories"""
    class Meta:
        model = ItemCategory
        fields = ['id', 'name', 'code', 'description']
        read_only_fields = ['id']


# ============================================================================
# ITEM SERIALIZERS
# ============================================================================

class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing items"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'code', 'department', 'department_name',
                  'category', 'category_name', 'unit', 'source_type', 
                  'source_type_display', 'total_stock', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_total_stock(self, obj):
        # Sum up inventory across all stores
        return sum(inv.quantity_on_hand for inv in obj.batch_set.all())


class ItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for item"""
    department = DepartmentListSerializer(read_only=True)
    category = ItemCategoryListSerializer(read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    university_master_item_detail = serializers.SerializerMethodField()
    batches_count = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'code', 'department', 'category', 
                  'specifications', 'unit', 'source_type', 'source_type_display',
                  'university_master_item', 'university_master_item_detail',
                  'batches_count', 'total_stock', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_university_master_item_detail(self, obj):
        if obj.university_master_item:
            return ItemListSerializer(obj.university_master_item).data
        return None
    
    def get_batches_count(self, obj):
        return obj.batch_set.count()
    
    def get_total_stock(self, obj):
        return sum(inv.quantity_on_hand for inv in obj.batch_set.all())


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating items"""
    class Meta:
        model = Item
        fields = ['id', 'name', 'code', 'department', 'category', 
                  'specifications', 'unit', 'source_type', 
                  'university_master_item', 'is_active']
        read_only_fields = ['id']
    
    def validate(self, attrs):
        # If source is university store, must have master item
        if attrs.get('source_type') == 'UNIVERSITY_STORE' and not attrs.get('university_master_item'):
            raise serializers.ValidationError(
                "University master item is required when source type is 'From University Store'"
            )
        return attrs


# ============================================================================
# STORE SERIALIZERS
# ============================================================================

class StoreListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing stores"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    store_type_display = serializers.CharField(source='get_store_type_display', read_only=True)
    parent_store_name = serializers.CharField(source='parent_store.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'code', 'store_type', 'store_type_display',
                  'department', 'department_name', 'parent_store', 'parent_store_name',
                  'location', 'incharge_name', 'incharge_contact', 'created_at']
        read_only_fields = ['id', 'created_at']


class StoreDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for store"""
    department = DepartmentListSerializer(read_only=True)
    store_type_display = serializers.CharField(source='get_store_type_display', read_only=True)
    parent_store_detail = serializers.SerializerMethodField()
    registers_count = serializers.SerializerMethodField()
    inventory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'code', 'store_type', 'store_type_display',
                  'department', 'parent_store', 'parent_store_detail',
                  'location', 'incharge_name', 'incharge_contact',
                  'registers_count', 'inventory_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_parent_store_detail(self, obj):
        if obj.parent_store:
            return StoreListSerializer(obj.parent_store).data
        return None
    
    def get_registers_count(self, obj):
        return obj.registers.count()
    
    def get_inventory_count(self, obj):
        return obj.inventory.count()


class StoreCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating stores"""
    class Meta:
        model = Store
        fields = ['id', 'name', 'code', 'store_type', 'department',
                  'parent_store', 'location', 'incharge_name', 'incharge_contact']
        read_only_fields = ['id']


# ============================================================================
# STOCK REGISTER SERIALIZERS
# ============================================================================

class StockRegisterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing registers"""
    store_name = serializers.CharField(source='store.name', read_only=True)
    register_type_display = serializers.CharField(source='get_register_type_display', read_only=True)
    entries_count = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField(method_name='get_link')

    class Meta:
        model = StockRegister
        fields = [
            'id', 'register_name', 'register_number', 'register_type',
            'register_type_display', 'store', 'store_name',
            'entries_count', 'is_active', 'created_at', 'link'
        ]
        read_only_fields = ['id', 'register_number', 'created_at']

    def get_entries_count(self, obj):
        return obj.entries.count()

    def get_link(self, obj):
        """
        Returns direct hyperlink to the StockRegister PDF download action.
        Example: /api/stock-registers/<id>/download-pdf/
        """
        request = self.context.get('request')
        if request:
            return reverse('stockregister-download-pdf', args=[obj.id], request=request)
        return None


class StockRegisterDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for register"""
    store = StoreListSerializer(read_only=True)
    register_type_display = serializers.CharField(source='get_register_type_display', read_only=True)
    entries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StockRegister
        fields = ['id', 'register_name', 'register_number', 'register_type',
                  'register_type_display', 'store', 'entries_count',
                  'is_active', 'created_at']
        read_only_fields = ['id', 'register_number', 'created_at']
    
    def get_entries_count(self, obj):
        return obj.entries.count()


class StockRegisterCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating registers"""
    class Meta:
        model = StockRegister
        fields = ['id', 'register_name', 'register_number', 'register_type', 
                  'store', 'is_active']
        read_only_fields = ['id', 'register_number']


# ============================================================================
# INSPECTION CERTIFICATE SERIALIZERS
# ============================================================================

class InspectionItemSerializer(serializers.ModelSerializer):
    """Serializer for inspection items"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)

    class Meta:
        model = InspectionItem
        fields = [
            'id',
            'item',
            'item_name',
            'item_code',
            'tendered_quantity',
            'accepted_quantity',
            'rejected_quantity',
            'manufacture_date',
            'warranty_period_months',
            'feedback'
        ]
        read_only_fields = ['id']


class InspectionCertificateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing certificates"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    register_name = serializers.CharField(source='stock_register.register_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    pdf_link = serializers.SerializerMethodField() 
    
    class Meta:
        model = InspectionCertificate
        fields = ['id', 'certificate_number', 'issued_on', 'issued_to',
                  'contractor', 'indenter', 'consignee', 'department', 
                  'department_name', 'date_of_delivery', 'delivery_status',
                  'stock_register', 'register_name',
                  'items_count', 'remarks', 'created_at', 'pdf_link']
        read_only_fields = ['id', 'created_at']
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_pdf_link(self, obj):
        request = self.context.get('request')
        if request:
            return reverse('inspectioncertificate-download-pdf', args=[obj.id], request=request)
        return None


class InspectionCertificateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for certificate"""
    department = DepartmentListSerializer(read_only=True)
    stock_register = StockRegisterListSerializer(read_only=True)
    items = InspectionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = InspectionCertificate
        fields = ['id', 'certificate_number', 'issued_on', 'issued_to',
                  'contractor', 'indenter', 'consignee', 'department',
                  'date_of_delivery', 'delivery_status',
                  'stock_register', 'items', 'remarks', 'created_at']
        read_only_fields = ['id', 'created_at']


class InspectionCertificateCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating certificates"""
    items = InspectionItemSerializer(many=True, required=False)
    
    class Meta:
        model = InspectionCertificate
        fields = ['id', 'certificate_number', 'issued_on', 'issued_to',
                  'contractor', 'indenter', 'consignee', 'department',
                  'date_of_delivery', 'delivery_status', 'stock_register',
                  'items', 'remarks']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        inspection = InspectionCertificate.objects.create(**validated_data)
        
        for item_data in items_data:
            InspectionItem.objects.create(inspection=inspection, **item_data)
        
        return inspection
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            # Clear existing items and create new ones
            instance.items.all().delete()
            for item_data in items_data:
                InspectionItem.objects.create(inspection=instance, **item_data)
        
        return instance


# ============================================================================
# BATCH SERIALIZERS
# ============================================================================

class BatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing batches"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    source_store_name = serializers.CharField(source='source_store.name', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    
    class Meta:
        model = Batch
        fields = ['id', 'batch_number', 'item', 'item_name', 'item_code',
                  'source_type', 'source_type_display', 'source_store', 
                  'source_store_name', 'total_quantity', 'current_quantity',
                  'warranty_expiry_date', 'expiry_date', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class BatchDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for batch"""
    item = ItemListSerializer(read_only=True)
    source_store = StoreListSerializer(read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    inspection_item_detail = serializers.SerializerMethodField()
    transfer_item_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = ['id', 'batch_number', 'item', 'source_type', 'source_type_display',
                  'source_store', 'inspection_item', 'inspection_item_detail',
                  'transfer_item', 'transfer_item_detail', 'total_quantity', 
                  'current_quantity', 'warranty_period_months', 'warranty_expiry_date',
                  'expected_life_years', 'manufacture_date', 'expiry_date',
                  'batch_specifications', 'remarks', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_inspection_item_detail(self, obj):
        if obj.inspection_item:
            return InspectionItemSerializer(obj.inspection_item).data
        return None
    
    def get_transfer_item_detail(self, obj):
        # Will implement when TransferNoteItem serializer is ready
        return None


class BatchCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating batches"""
    class Meta:
        model = Batch
        fields = ['id', 'batch_number', 'item', 'source_type', 'source_store',
                  'inspection_item', 'transfer_item', 'total_quantity', 
                  'current_quantity', 'warranty_period_months', 'warranty_expiry_date',
                  'expected_life_years', 'manufacture_date', 'expiry_date',
                  'batch_specifications', 'remarks', 'is_active']
        read_only_fields = ['id']


# ============================================================================
# STOCK ENTRY SERIALIZERS
# ============================================================================

class StockEntryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing stock entries"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, allow_null=True)
    
    class Meta:
        model = StockEntry
        fields = ['id', 'entry_number', 'entry_type', 'entry_type_display',
                  'entry_date', 'item', 'item_name', 'item_code', 'batch', 
                  'batch_number', 'quantity', 'balance', 'store', 'store_name',
                  'from_store', 'to_store', 'to_location', 'created_at']
        read_only_fields = ['id', 'entry_number', 'entry_date', 'created_at']


class StockEntryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for stock entry"""
    item = ItemListSerializer(read_only=True)
    batch = BatchListSerializer(read_only=True)
    store = StoreListSerializer(read_only=True)
    from_store = StoreListSerializer(read_only=True)
    to_store = StoreListSerializer(read_only=True)
    to_location = LocationListSerializer(read_only=True)
    stock_register = StockRegisterListSerializer(read_only=True)
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)
    
    class Meta:
        model = StockEntry
        fields = ['id', 'entry_number', 'entry_type', 'entry_type_display',
                  'entry_date', 'item', 'batch', 'quantity', 'balance',
                  'store', 'from_store', 'to_store', 'to_location',
                  'stock_register', 'inspection_certificate', 'transfer_note',
                  'transfer_note_item', 'adjustment_reason', 'reference_entry',
                  'remarks', 'created_at']
        read_only_fields = ['id', 'entry_number', 'entry_date', 'created_at']


class StockEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock entries (mainly adjustments)"""
    class Meta:
        model = StockEntry
        fields = ['id', 'entry_type', 'item', 'batch', 'quantity', 'balance',
                  'store', 'from_store', 'to_store', 'to_location',
                  'stock_register', 'adjustment_reason', 'reference_entry', 'remarks']
        read_only_fields = ['id', 'entry_number', 'entry_date']
    
    def validate(self, attrs):
        if attrs.get('entry_type') == 'ADJUSTMENT' and not attrs.get('adjustment_reason'):
            raise serializers.ValidationError(
                "Adjustment reason is required for adjustment entries"
            )
        return attrs


# ============================================================================
# STORE INVENTORY SERIALIZERS
# ============================================================================

class StoreInventoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing inventory"""
    store_name = serializers.CharField(source='store.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    item_name = serializers.CharField(source='batch.item.name', read_only=True)
    item_code = serializers.CharField(source='batch.item.code', read_only=True)
    
    class Meta:
        model = StoreInventory
        fields = ['id', 'store', 'store_name', 'batch', 'batch_number',
                  'item_name', 'item_code', 'quantity_on_hand', 
                  'quantity_allocated', 'quantity_qr_tagged', 'last_updated']
        read_only_fields = ['id', 'last_updated']


class StoreInventoryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for inventory"""
    store = StoreListSerializer(read_only=True)
    batch = BatchDetailSerializer(read_only=True)
    
    class Meta:
        model = StoreInventory
        fields = ['id', 'store', 'batch', 'quantity_on_hand', 
                  'quantity_allocated', 'quantity_qr_tagged', 'last_updated']
        read_only_fields = ['id', 'last_updated']

class TransferNoteItemSerializer(serializers.ModelSerializer):
    """Serializer for transfer note items"""
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)

    class Meta:
        model = TransferNoteItem
        fields = [
            'id', 'batch', 'batch_number', 'item', 'item_name', 'item_code',
            'quantity_sent', 'quantity_received',
            'is_acknowledged', 'acknowledged_by', 'acknowledged_at', 'remarks'
        ]
        read_only_fields = ['id', 'is_acknowledged', 'acknowledged_by', 'acknowledged_at']



class TransferNoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing transfer notes"""
    from_store_name = serializers.CharField(source='from_store.name', read_only=True)
    to_store_name = serializers.CharField(source='to_store.name', read_only=True, allow_null=True)
    to_location_name = serializers.CharField(source='to_location.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferNote
        fields = ['id', 'transfer_note_number', 'transfer_date', 'from_store',
                  'from_store_name', 'to_store', 'to_store_name', 'to_location',
                  'to_location_name', 'status', 'status_display', 'items_count',
                  'created_at']
        read_only_fields = ['id', 'transfer_note_number', 'created_at']
    
    def get_items_count(self, obj):
        return obj.items.count()


class TransferNoteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for transfer note"""
    from_store = StoreListSerializer(read_only=True)
    to_store = StoreListSerializer(read_only=True)
    to_location = LocationListSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = TransferNoteItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = TransferNote
        fields = ['id', 'transfer_note_number', 'transfer_date', 'from_store',
                  'to_store', 'to_location', 'status', 
                  'status_display', 'items', 'remarks', 'created_at', 'updated_at']
        read_only_fields = ['id', 'transfer_note_number', 'created_at', 'updated_at']


class TransferNoteItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transfer note items (input only)"""
    class Meta:
        model = TransferNoteItem
        fields = ['batch', 'item', 'quantity_sent', 'remarks']


class TransferNoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating transfer notes"""
    items = TransferNoteItemCreateSerializer(many=True, required=False)

    class Meta:
        model = TransferNote
        fields = ['id', 'transfer_note_number', 'transfer_date', 'from_store',
                  'to_store', 'to_location', 'status', 'items', 'remarks']
        read_only_fields = ['id', 'transfer_note_number']

    def validate(self, attrs):
        if not attrs.get('to_store') and not attrs.get('to_location'):
            raise serializers.ValidationError(
                "Either 'to_store' or 'to_location' must be specified"
            )
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # Auto-generate transfer note number
        last_note = TransferNote.objects.order_by('-id').first()
        if last_note:
            last_number = int(last_note.transfer_note_number.split('-')[-1])
            new_number = f"TN-{last_number + 1:04d}"
        else:
            new_number = "TN-0001"
        validated_data['transfer_note_number'] = new_number

        transfer_note = TransferNote.objects.create(**validated_data)

        for item_data in items_data:
            TransferNoteItem.objects.create(transfer_note=transfer_note, **item_data)

        return transfer_note

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                TransferNoteItem.objects.create(transfer_note=instance, **item_data)

        return instance


class TransferNoteAcknowledgmentSerializer(serializers.Serializer):
    """Serializer for acknowledging transfer note items with stock register"""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items with acknowledgment details"
    )

    def validate_items(self, value):
        for item in value:
            if 'item_id' not in item:
                raise serializers.ValidationError("Each item must have 'item_id'")
            if 'quantity_received' not in item:
                raise serializers.ValidationError("Each item must have 'quantity_received'")
            if 'stock_register' not in item:
                raise serializers.ValidationError("Each item must have 'stock_register' (ID)")

            qty_received = item.get('quantity_received', 0)
            qty_returned = item.get('quantity_returned', 0)

            if qty_received < 0 or qty_returned < 0:
                raise serializers.ValidationError("Quantities cannot be negative")

            # If item is returned, a reason is required
            if qty_returned > 0 and not item.get('return_reason'):
                raise serializers.ValidationError(
                    "Please provide 'return_reason' for returned items"
                )

        return value

    def create(self, validated_data):
        """Process acknowledgment for a transfer note"""
        transfer_note = self.context.get('transfer_note')
        user = None  # make sure user is passed in context

        if not transfer_note:
            raise serializers.ValidationError("Transfer note context is required")

        for item_data in validated_data['items']:
            # Get the TransferNoteItem using ID from payload
            try:
                tni = TransferNoteItem.objects.get(
                    id=item_data['item_id'],
                    transfer_note=transfer_note
                )
            except TransferNoteItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"TransferNoteItem with id {item_data['item_id']} not found in this transfer note"
                )

            # Update acknowledgment fields
            tni.is_acknowledged = True
            tni.quantity_received = item_data['quantity_received']
            tni.acknowledged_by = user
            tni.acknowledged_at = timezone.now()
            tni.remarks = item_data.get('remarks', '')
            tni.save()

            # Update store inventory for this batch
            store_inventory, created = StoreInventory.objects.get_or_create(
                batch=tni.batch,
                store=transfer_note.to_store,
                defaults={'quantity_on_hand': 0}
            )
            store_inventory.quantity_on_hand += tni.quantity_received
            store_inventory.save()

            # Create StockEntry and link to TransferNoteItem
            stock_entry = StockEntry.objects.create(
                entry_type='RECEIPT',
                item=tni.item,
                batch=tni.batch,
                quantity=tni.quantity_received,
                balance=store_inventory.quantity_on_hand,
                store=transfer_note.to_store,
                stock_register_id=item_data['stock_register'],
                reference_entry=None,
                remarks=item_data.get('remarks', '')
            )
            tni.receipt_entry = stock_entry
            tni.save()

        return transfer_note
# -----------------------------
# Requisition Item Serializer
# -----------------------------



class RequisitionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitionItem
        fields = [
            'id', 'item_name', 'item_specifications', 'requested_quantity',
            'approved_quantity', 'provided_quantity', 'received_quantity',
            'is_approved', 'is_rejected', 'reject_reason', 'item', 'batch'
        ]
        read_only_fields = ['approved_quantity', 'provided_quantity', 'received_quantity', 'item', 'batch']

# -----------------------------
# Requisition Serializer
# -----------------------------

class RequisitionItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitionItem
        fields = ['item_name', 'item_specifications', 'requested_quantity']

    def validate_requested_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Requested quantity must be greater than zero.")
        return value
    
class RequisitionCreateSerializer(serializers.ModelSerializer):
    items = RequisitionItemCreateSerializer(many=True)

    class Meta:
        model = Requisition
        fields = ['requisition_no', 'department', 'from_store', 'main_store', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        requisition = Requisition.objects.create(**validated_data)
        for item in items_data:
            RequisitionItem.objects.create(requisition=requisition, **item)
        return requisition
    
class RequisitionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitionItem
        fields = [
            'id', 'item_name', 'item_specifications',
            'requested_quantity', 'approved_quantity',
            'provided_quantity', 'received_quantity',
            'is_approved', 'is_rejected', 'reject_reason'
        ]

class RequisitionSerializer(serializers.ModelSerializer):
    items = RequisitionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Requisition
        fields = [
            'id', 'requisition_no', 'department', 'from_store', 'main_store',
            'status', 'created_by', 'created_at', 'items'
        ]

class RequisitionItemProcessSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()  # RequisitionItem ID
    provided_quantity = serializers.IntegerField(min_value=0)
    reject_reason = serializers.CharField(required=False, allow_blank=True)
    main_stock_register = serializers.IntegerField()  # StockRegister ID
    batch_id = serializers.IntegerField(required=True)  # Batch ID from which stock is allocated

    class Meta:
        model = RequisitionItem
        fields = ['id', 'provided_quantity', 'reject_reason', 'main_stock_register', 'batch_id']

    def validate(self, data):
        # If quantity is 0, reject_reason is required
        if data['provided_quantity'] == 0 and not data.get('reject_reason'):
            raise serializers.ValidationError("Provide a reject reason if provided quantity is 0.")
        return data
    
class RequisitionAcknowledgmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requisition
        fields = ['id', 'status', 'acknowledged_by', 'acknowledged_at']
        read_only_fields = ['id', 'status', 'acknowledged_by', 'acknowledged_at']