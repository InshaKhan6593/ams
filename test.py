from django.db import models
from django.contrib.auth.models import User
import uuid


class Department(models.Model):
    """University departments including Directorate of Work and Service"""
    department_code = models.CharField(max_length=50, unique=True)
    department_name = models.CharField(max_length=255)
    is_main_university_store = models.BooleanField(
        default=False, 
        help_text='Mark if this is Directorate of Work and Service'
    )
    parent_department = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    hod_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.department_code} - {self.department_name}"

class Store(models.Model):
    """Main stores and sub-stores within departments"""
    STORE_TYPE = [
        ('MAIN_UNIVERSITY', 'Main University Store'),
        ('MAIN_DEPARTMENT', 'Main Department Store'),
        ('SUB_STORE', 'Sub Store'),
    ]

    store_code = models.CharField(max_length=50, unique=True)
    store_name = models.CharField(max_length=255)
    store_type = models.CharField(max_length=20, choices=STORE_TYPE)
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT, 
        related_name='stores'
    )
    parent_store = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sub_stores'
    )
    incharge_name = models.CharField(max_length=255)
    location_building = models.CharField(max_length=255, blank=True)
    location_room = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.store_code} - {self.store_name}"
    
class StockRegister(models.Model):
    """Stock registers for different types of items"""
    REGISTER_TYPE = [
        ('DEADSTOCK', 'Dead Stock Register'),
        ('CONSUMABLE', 'Consumable Register'),
        ('EQUIPMENT', 'Equipment Register'),
    ]

    register_name = models.CharField(max_length=255)
    register_number = models.CharField(max_length=50, unique=True)
    register_type = models.CharField(max_length=20, choices=REGISTER_TYPE)
    store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name='registers'
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.register_number} - {self.register_name}"
    
class Location(models.Model):
    """Non-store locations like offices, rooms, labs where items are deployed"""
    location_code = models.CharField(max_length=50, unique=True)
    location_name = models.CharField(max_length=255)
    location_type = models.CharField(
        max_length=100, 
        help_text='Office, Lab, Room, etc.'
    )
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    building = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    incharge_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location_code} - {self.location_name}"
    
class ItemCategory(models.Model):
    """Categories for organizing items"""
    category_code = models.CharField(max_length=50, unique=True)
    category_name = models.CharField(max_length=255)
    parent_category = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category_code} - {self.category_name}"
    
class Item(models.Model):
    """Master item definition"""
    ITEM_TYPE = [
        ('DEADSTOCK', 'Dead Stock'),
        ('CONSUMABLE', 'Consumable'),
        ('EQUIPMENT', 'Equipment'),
        ('FURNITURE', 'Furniture'),
        ('BOOKS', 'Books'),
    ]

    item_code = models.CharField(max_length=100, unique=True)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE)
    category = models.ForeignKey(
        ItemCategory, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT, 
        help_text='Department that manages this item'
    )
    
    # Specifications
    base_specifications = models.JSONField(
        default=dict, 
        help_text='Common specs like brand, model, etc.'
    )
    unit_of_measurement = models.CharField(max_length=50, default='Nos')
    
    # Thresholds for alerts
    minimum_stock_level = models.PositiveIntegerField(
        default=0, 
        help_text='Alert when stock falls below this'
    )
    reorder_level = models.PositiveIntegerField(default=0)
    
    # Linking to university store items
    linked_university_item = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='If item created from university store distribution'
    )
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.item_code} - {self.item_name}"
    
class Batch(models.Model):
    """
    Core tracking unit for inventory.
    Each inspection creates a batch. Items from same purchase with same specs.
    QR codes are generated on-demand from batches.
    """
    SOURCE_TYPE = [
        ('DEPARTMENTAL_PURCHASE', 'Departmental Purchase'),
        ('UNIVERSITY_STORE', 'University Store Distribution'),
    ]

    batch_number = models.CharField(max_length=100, unique=True)
    item = models.ForeignKey(
        Item, 
        on_delete=models.PROTECT, 
        related_name='batches'
    )
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE)
    source_store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name='batches_created',
        help_text='Store that created/received this batch'
    )
    
    # If source is university store distribution
    university_batch = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Link to parent university store batch if distributed'
    )
    
    # Quantities
    total_quantity = models.PositiveIntegerField(
        help_text='Total quantity received in this batch'
    )
    current_quantity = models.PositiveIntegerField(
        help_text='Current quantity available (unassigned units)'
    )
    
    # QR tracking metrics
    qr_tagged_quantity = models.PositiveIntegerField(
        default=0,
        help_text='Number of units that have QR codes generated'
    )
    
    # Purchase details
    purchase_order_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    supplier_name = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    # Warranty & lifecycle
    warranty_period_months = models.PositiveIntegerField(default=0)
    warranty_expiry_date = models.DateField(null=True, blank=True)
    expected_life_years = models.PositiveIntegerField(default=0)
    
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Batch-specific specifications
    batch_specifications = models.JSONField(
        default=dict, 
        help_text='Specific specs for this batch'
    )
    
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        qr_info = f"({self.qr_tagged_quantity}/{self.total_quantity} QR-tagged)"
        return f"{self.batch_number} - {self.item.item_name} {qr_info}"
    
    @property
    def available_for_qr_generation(self):
        """Units that can still have QR codes generated"""
        return self.total_quantity - self.qr_tagged_quantity
    
class QRCode(models.Model):
    qr_string = models.CharField(max_length=255, unique=True)  # the actual encoded text
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, related_name='qrcodes')
    item = models.ForeignKey('Item', on_delete=models.PROTECT, related_name='qrcodes')
    current_store = models.ForeignKey('Store', on_delete=models.PROTECT, null=True, blank=True)
    current_location = models.ForeignKey('Location', on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('IN_STOCK', 'In Stock'),
        ('IN_USE', 'In Use'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('DAMAGED', 'Damaged'),
        ('WRITTEN_OFF', 'Written Off'),
    ], default='IN_STOCK')
    last_inspection = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.item_name} [{self.qr_string}]"

    def update_location(self, store=None, location=None):
        """Update current location and sync automatically"""
        self.current_store = store
        self.current_location = location
        self.save(update_fields=['current_store', 'current_location', 'updated_at'])
    
class TransferNote(models.Model):
    """
    Transfer note for item movement between stores or to locations.
    Handles both QR-tracked and non-QR-tracked items.
    """
    TRANSFER_TYPE = [
        ('STORE_TO_STORE', 'Store to Store'),
        ('STORE_TO_LOCATION', 'Store to Location (Issue)'),
        ('UNIVERSITY_TO_DEPARTMENT', 'University Store to Department'),
    ]

    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('IN_STOCK', 'In Stock'),
        ('ISSUED', 'Issued'),
        ('IN_USE', 'In Use'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('DAMAGED', 'Damaged'),
        ('WRITTEN_OFF', 'Written Off'),
        ('LOST', 'Lost'),
    ]   

    transfer_number = models.CharField(max_length=100, unique=True)
    transfer_type = models.CharField(max_length=30, choices=TRANSFER_TYPE)
    
    # Source and destination
    from_store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name='outgoing_transfers'
    )
    to_store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='incoming_transfers'
    )
    to_location = models.ForeignKey(
        Location, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text='End location (for issues/deployments)'
    )
    
    # Dates
    transfer_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='INITIATED'
    )
    
    # Acknowledgment workflow
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='acknowledged_transfers'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledgment_remarks = models.TextField(blank=True)
    
    # Transport details
    transporter_name = models.CharField(max_length=255, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    
    remarks = models.TextField(blank=True)
    
    issued_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='issued_transfers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TN-{self.transfer_number}"
    
class TransferItem(models.Model):
    """
    Items in transfer note.
    
    INDUSTRIAL APPROACH - FLEXIBLE TRACKING:
    ========================================
    1. Always specify quantity (fundamental requirement)
    2. Optionally attach specific QR codes (for accountable items)
    3. System validates: quantity_sent >= qr_codes.count()
    4. Untracked quantity = quantity_sent - qr_codes.count()
    
    Example: Transfer 5 Core i5 processors
    - 2 have QR codes → attach them
    - 3 don't have QR codes → just send as quantity
    - quantity_sent = 5
    - qr_codes = [QR-001, QR-002]
    - System tracks: 2 individually, 3 as bulk
    """
    
    transfer = models.ForeignKey(
        TransferNote, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    
    # ALWAYS REQUIRED: Total quantity being sent
    quantity_sent = models.PositiveIntegerField(
        help_text='Total quantity being transferred from this batch'
    )
    quantity_received = models.PositiveIntegerField(
        default=0,
        help_text='Quantity confirmed received'
    )
    quantity_damaged = models.PositiveIntegerField(
        default=0,
        help_text='Quantity damaged during transfer'
    )
    
    # OPTIONAL: Specific QR codes (if any exist and store wants to track)
    specific_qr_codes = models.ManyToManyField(
        QRCode, 
        blank=True,
        help_text='QR-tagged units in this transfer (can be 0, some, or all)'
    )
    
    # Track what's NOT QR-tagged
    @property
    def quantity_without_qr(self):
        """Quantity being sent without individual QR tracking"""
        return self.quantity_sent - self.specific_qr_codes.count()
    
    # Option to generate QR codes at destination
    generate_qr_at_destination = models.BooleanField(
        default=False,
        help_text='Generate QR codes for untracked quantity at receiving store'
    )
    
    remarks = models.TextField(blank=True)


    def __str__(self):
        qr_count = self.specific_qr_codes.count()
        if qr_count > 0:
            return f"{self.transfer.transfer_number} - {self.item.item_code} (Qty: {self.quantity_sent}, {qr_count} QR-tagged)"
        return f"{self.transfer.transfer_number} - {self.item.item_code} (Qty: {self.quantity_sent}, bulk)"


class InspectionCertificate(models.Model):
    """Inspection certificate for incoming items"""
    DELIVERY_STATUS_TYPE = [
        ('PARTIAL', 'Partial Delivery'),
        ('FULL', 'Full Delivery'),
    ]

    certificate_number = models.CharField(max_length=255, unique=True)
    
    # Basic details
    issued_on = models.DateField()
    issued_to = models.CharField(
        max_length=255, 
        help_text='Department/Store receiving'
    )
    receiving_store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name='inspections'
    )
    
    # Parties involved
    indenter = models.CharField(
        max_length=255, 
        help_text='Person who requested'
    )
    consignee = models.CharField(
        max_length=255, 
        help_text='Person receiving'
    )

    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    
    # Delivery details
    date_of_delivery = models.DateField()
    delivery_status = models.CharField(
        max_length=20, 
        choices=DELIVERY_STATUS_TYPE
    )
    
    # Stock register where entries will be made
    stock_register = models.ForeignKey(
        StockRegister, 
        on_delete=models.PROTECT, 
        related_name='inspections'
    )

    remarks = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_inspections'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IC-{self.certificate_number}"

class InspectionItem(models.Model):
    """Items in inspection certificate - creates batches upon approval"""
    inspection = models.ForeignKey(
        InspectionCertificate, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    
    # Link to existing item or create new
    item = models.ForeignKey(
        Item, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    should_create_new_item = models.BooleanField(default=False)
    
    # Item details
    item_description = models.TextField()
    specifications = models.JSONField(default=dict)
    hsn_code = models.CharField(max_length=50, blank=True)
    
    # Quantities
    tendered_quantity = models.PositiveIntegerField()
    accepted_quantity = models.PositiveIntegerField()
    rejected_quantity = models.PositiveIntegerField()
    unit_of_measurement = models.CharField(max_length=50, default='Nos')

    feedback = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inspection.certificate_number} - {self.item_description}"

class StoreInventory(models.Model):
    """
    Current inventory snapshot for each store.
    Tracks batch-level quantities (not individual QR codes).
    """
    store = models.ForeignKey(Store, on_delete=models.PROTECT)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    
    # Total quantity in this store for this batch
    quantity = models.PositiveIntegerField(default=0)
    
    # For QR-enabled items: count of QR codes in this store
    qr_code_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of QR-tagged units (if QR tracking enabled)'
    )
    
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.store.store_code} - {self.item.item_code} - Batch: {self.batch.batch_number} (Qty: {self.quantity})"



class StockEntry(models.Model):
    """
    Stock register entries for all inventory movements.
    Immutable ledger for audit trail.
    """
    ENTRY_TYPE = [
        ('RECEIPT', 'Receipt'),
        ('ISSUE', 'Issue'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
        ('QR_GENERATION', 'QR Code Generated'),
    ]

    entry_number = models.CharField(max_length=50, unique=True)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE)
    entry_date = models.DateField()
    
    # Item and batch
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    
    # Quantities
    quantity = models.PositiveIntegerField(
        help_text='Quantity in this transaction'
    )
    balance = models.PositiveIntegerField(
        help_text='Running balance after this entry'
    )
    
    # Source and destination
    from_store = models.ForeignKey(
        Store, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='issued_entries'
    )
    to_store = models.ForeignKey(
        Store, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='received_entries'
    )
    to_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='location_entries'
    )
    
    # Register details
    stock_register = models.ForeignKey(
        StockRegister, 
        on_delete=models.PROTECT, 
        related_name='entries'
    )
    page_number = models.PositiveIntegerField()
    entry_line_number = models.PositiveIntegerField()
    
    # References
    transfer_note = models.ForeignKey(
        TransferNote, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    inspection_certificate = models.ForeignKey(
        InspectionCertificate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Financial
    unit_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    remarks = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entry_number} - {self.entry_type} - {self.item.item_code}"
    

