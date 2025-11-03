from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid
from .helper_functions import *

class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, blank=True)
    is_main_university_store = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_department_code(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.code}'

class Location(models.Model):
    LOCATION_TYPE = [
        ('ROOM', 'Room'),
        ('AUDITORIUM', 'Auditorium'),
        ('LAB', 'Laboratory'),
        ('OFFICE', 'Office'),
        ('REPAIR_CENTER', 'Repair Center'),
        ('HOSTEL', 'Hostel'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    location_type = models.CharField(max_length=30, choices=LOCATION_TYPE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='locations')
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.location_type})"

class Store(models.Model):
    STORE_TYPE = [
        ('MAIN', 'Main Department Store'),
        ('SUB', 'Sub Store')
    ]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    store_type = models.CharField(max_length=10, choices=STORE_TYPE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    parent_store = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    location = models.TextField()
    incharge_name = models.CharField(max_length=255)
    incharge_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.code} - {self.name}'

class StockRegister(models.Model):
    REGISTER_TYPE = [
        ('DEADSTOCK', 'Dead Stock Register'),
        ('CONSUMABLE', 'Consumable Register'),
        ('EQUIPMENT', 'Equipment Register')
    ]

    register_name = models.CharField(max_length=255)
    register_number = models.CharField(max_length=50, unique=True, blank=True)
    register_type = models.CharField(max_length=20, choices=REGISTER_TYPE)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='registers')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.register_number:
            self.register_number = generate_register_number(self.store.code, self.register_type)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.register_name} - {self.register_number} ({self.get_register_type_display()})'

class ItemCategory(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    SOURCE_TYPE = [
        ('DEPT_PURCHASE', 'Department Purchase'),
        ('UNIVERSITY_STORE', 'From University Store')
    ]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='items')
    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT)
    specifications = models.JSONField(default=dict)
    unit = models.CharField(max_length=50)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE)
    university_master_item = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['code', 'department']]

    def __str__(self):
        return f'{self.code} - {self.name} ({self.department})'

class InspectionCertificate(models.Model):
    DELIVERY_STATUS_TYPE = [
        ('PART', 'Partial'),
        ('FULL', 'Full')
    ]

    certificate_number = models.CharField(max_length=255, unique=True)
    issued_on = models.DateField()
    issued_to = models.CharField(max_length=255)
    contractor = models.CharField(max_length=255)
    indenter = models.CharField(max_length=255)
    consignee = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    date_of_delivery = models.DateField()
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_TYPE)
    stock_register = models.ForeignKey(
        StockRegister,
        on_delete=models.PROTECT,
        related_name='inspection_certificates',
        help_text='Register where entries will be made'
    )
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.certificate_number}'

class InspectionItem(models.Model):
    inspection = models.ForeignKey(
        'InspectionCertificate',
        on_delete=models.CASCADE,
        related_name='items'
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    tendered_quantity = models.PositiveIntegerField()
    accepted_quantity = models.PositiveIntegerField()
    rejected_quantity = models.PositiveIntegerField()
    manufacture_date = models.DateField(null=True, blank=True)
    warranty_period_months = models.PositiveIntegerField(default=0)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f'{self.item.name} - {self.inspection.certificate_number}'

    def clean(self):
        if self.item and self.item.department != self.inspection.department:
            raise ValidationError(
                f'{self.item} does not belong to specified department in Inspection Certificate'
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Batch(models.Model):
    SOURCE_TYPE = [
        ('DEPARTMENTAL_PURCHASE', 'Departmental Purchase'),
        ('UNIVERSITY_STORE', 'University Store Distribution'),
    ]

    batch_number = models.CharField(max_length=100, unique=True)
    inspection_item = models.OneToOneField(
        'InspectionItem',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='batch'
    )
    transfer_item = models.OneToOneField(
        'TransferNoteItem',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='created_batch'
    )
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE)
    source_store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='batches_created',
        help_text='Store that created/received this batch'
    )
    total_quantity = models.PositiveIntegerField(
        help_text='Total quantity received in this batch'
    )
    current_quantity = models.PositiveIntegerField(
        help_text='Current quantity available (unassigned units)'
    )
    warranty_period_months = models.PositiveIntegerField(default=0)
    warranty_expiry_date = models.DateField(null=True, blank=True)
    expected_life_years = models.PositiveIntegerField(default=0)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    batch_specifications = models.JSONField(
        default=dict,
        help_text='Specific specs for this batch'
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.source_type == 'DEPARTMENTAL_PURCHASE' and not self.inspection_item:
            raise ValidationError("Inspection item required for departmental purchase batch.")
        if self.source_type == 'UNIVERSITY_STORE' and not self.transfer_item:
            raise ValidationError("Transfer item required for university store distribution batch.")

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.source_type == 'DEPARTMENTAL_PURCHASE' and self.inspection_item:
                insp = self.inspection_item
                self.item = insp.item
                self.total_quantity = insp.accepted_quantity
                self.current_quantity = insp.accepted_quantity
            elif self.source_type == 'UNIVERSITY_STORE' and self.transfer_item:
                trans = self.transfer_item
                self.item = trans.item
                self.total_quantity = trans.accepted_quantity
                self.current_quantity = trans.accepted_quantity
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.batch_number} - {self.item.name}'

class StoreInventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='inventory')
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, related_name='inventories')
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_allocated = models.PositiveIntegerField(default=0)
    quantity_qr_tagged = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['store', 'batch']]

    def __str__(self):
        return f'{self.store.code} - (Batch: {self.batch.batch_number})'

class TransferNote(models.Model):
    """
    Transfer Note for moving items between stores - direct transfers without requisition
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('IN_TRANSIT', 'In Transit'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled')
    ]

    transfer_note_number = models.CharField(max_length=50, unique=True, editable=False)
    transfer_date = models.DateField()
    from_store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='transfers_out'
    )
    to_store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='transfers_in',
        null=True,
        blank=True
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transfers_to_location'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        to_ref = self.to_store.code if self.to_store else self.to_location.code
        return f'{self.transfer_note_number}: {self.from_store.code} -> {to_ref}'

class TransferNoteItem(models.Model):
    """
    Items in transfer note - tracks batch and quantities
    """
    transfer_note = models.ForeignKey(
        TransferNote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    batch = models.ForeignKey(
        'Batch',
        on_delete=models.PROTECT,
        related_name='transfer_items'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT
    )
    # Quantities
    quantity_sent = models.PositiveIntegerField(
        help_text="Total quantity sent from source store"
    )
    quantity_received = models.PositiveIntegerField(
        default=0,
        help_text="Quantity actually received at destination"
    )
    
    # Acknowledgment tracking
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_transfers',
        help_text="User who acknowledged receipt"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # QR-tagged assets (optional)
    qr_tags = models.ManyToManyField(
        'AssetTag',
        blank=True,
        related_name='transfer_sent',
        help_text='QR-tagged assets from this batch included in transfer'
    )
    
    # Stock entry references (created automatically)
    issue_entry = models.ForeignKey(
        'StockEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_issue'
    )
    receipt_entry = models.ForeignKey(
        'StockEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_receipt'
    )
    
    remarks = models.TextField(blank=True)

    def clean(self):
        # Validate QR tags belong to batch
        for tag in self.qr_tags.all():
            if tag.batch != self.batch:
                raise ValidationError(
                    f"QR tag {tag.tag_number} does not belong to batch {self.batch.batch_number}"
                )
        
        # Validate acknowledgment quantity
        if self.is_acknowledged and self.quantity_received > self.quantity_sent:
            raise ValidationError(
                f"Quantity received ({self.quantity_received}) cannot exceed quantity sent ({self.quantity_sent})"
            )

    def __str__(self):
        return f"{self.transfer_note.transfer_note_number} - {self.batch.batch_number} ({self.quantity_sent})"

class StockEntry(models.Model):
    """
    Stock register entries - automatically created for receipts, issues, and adjustments
    """
    ENTRY_TYPE = [
        ('RECEIPT', 'Receipt'),
        ('ISSUE', 'Issue'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    entry_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE)
    entry_date = models.DateField(auto_now_add=True)
    
    # Item and batch tracking
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Batch reference for tracking'
    )
    
    quantity = models.IntegerField(help_text='Positive for receipt, negative for issue')
    balance = models.PositiveIntegerField(help_text='Balance after this entry')
    
    # Store tracking
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='stock_entries',
        help_text='Store where entry is recorded'
    )
    
    # References to source documents
    from_store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_stock_entries'
    )
    to_store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_stock_entries'
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_stock_entries'
    )
    
    # Source documents
    inspection_certificate = models.ForeignKey(
        InspectionCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_entries'
    )
    transfer_note = models.ForeignKey(
        TransferNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_entries'
    )
    transfer_note_item = models.ForeignKey(
        TransferNoteItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_entries'
    )
    
    # Register reference
    stock_register = models.ForeignKey(
        StockRegister,
        on_delete=models.PROTECT,
        related_name='entries'
    )
    
    # For adjustments
    adjustment_reason = models.TextField(
        blank=True,
        help_text='Reason for adjustment entry'
    )
    reference_entry = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjusting_entries',
        help_text='Original entry being adjusted/corrected'
    )
    
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.entry_number} ({self.entry_type}) - {self.item.code} x {self.quantity}'

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stock Entries'

    def save(self, *args, **kwargs):
        # Automatically generate entry number if missing
        if not self.entry_number:
            prefix = 'SE'  # Stock Entry
            date_str = timezone.now().strftime('%Y%m%d')
            last_entry = StockEntry.objects.order_by('-id').first()
            next_id = 1 if not last_entry else last_entry.id + 1
            self.entry_number = f'{prefix}-{date_str}-{next_id:04d}'
        super().save(*args, **kwargs)

class Requisition(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('IN_TRANSIT', 'In Transit'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('RECEIVED', 'Received'),
        ('REJECTED', 'Rejected')
    ]

    requisition_no = models.CharField(max_length=100, unique=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.PROTECT)
    from_store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='requisitions_sent')
    main_store = models.ForeignKey('Store', on_delete=models.PROTECT, related_name='requisitions_received')  # Main Store
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions_acknowledged',
        help_text="User who acknowledged receipt"
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when requisition was acknowledged as received"
    )

    def mark_as_received(self, user):
        """
        Called by receiving store to acknowledge receipt.
        Updates status, acknowledged_by, and acknowledged_at.
        """
        self.status = 'RECEIVED'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()

class RequisitionItem(models.Model):
    requisition = models.ForeignKey('Requisition', on_delete=models.CASCADE, related_name='items')
    
    item_name = models.CharField(max_length=255)
    item_specifications = models.TextField(blank=True, null=True)
    
    requested_quantity = models.PositiveIntegerField()
    
    approved_quantity = models.PositiveIntegerField(default=0)
    provided_quantity = models.PositiveIntegerField(default=0)
    received_quantity = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    reject_reason = models.TextField(blank=True, null=True)

    main_stock_register = models.ForeignKey(StockRegister, on_delete=models.PROTECT, null=True)
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, null=True, blank=True)
    

    def save(self, *args, **kwargs):
        # Auto-mark approval/rejection
        if self.is_rejected:
            self.is_approved = False
            self.approved_quantity = 0
            self.provided_quantity = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} ({self.requested_quantity})"




class AssetTag(models.Model):
    pass