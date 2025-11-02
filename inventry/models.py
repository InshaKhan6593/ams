from django.db import models
from  django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid
from .helper_functions import *
import qrcode
from io import BytesIO
from django.core.files import File

class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, blank=True)
    is_main_university_store  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_department_code(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.code}'
    
class Store(models.Model):
    STORE_TYPE = [
        ('MAIN', 'Main Department Store'),
        ('SUB', 'Sub  Store')
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
    is_active  = models.BooleanField(default=True)

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
        ('DEPT_PURCHASE', 'Department  Purchase'),
        ('UNIVERSITY_STORE', 'From University Store')
    ]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='items')
    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT)
    specifications = models.JSONField(default=dict)
    unit = models.CharField(max_length=50) # pieces, kg, liters, etc.
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE)
    # if from university store, link to that item
    university_master_item = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['code', 'department']] 
    
    def __str__(self):
        return f'{self.code} - {self.name} ({self.department})'
    
class InspectionCertificate(models.Model):

    DELIVERY_STATUS_TYPE = [
        ('PART', 'partial'),
        ('FULL', 'full')
    ]

    certificate_number =  models.CharField(max_length=255, unique=True)
    issued_on = models.DateField()
    issued_to = models.CharField(max_length=255)
    contracter = models.CharField(max_length=255)
    indenter = models.CharField(max_length=255)
    consignee = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)

    date_of_delivery = models.DateField()
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_TYPE)

    stock_register = models.ForeignKey(
        StockRegister,
        on_delete=models.PROTECT,
        related_name='inspections',
        help_text='Register where entries will be made'
    )

    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

        
class InspectionItem(models.Model):
    inspection = models.ForeignKey(InspectionCertificate, on_delete=models.CASCADE, related_name='items')
    # Link  to Existing item or create new
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True)
    tendered_quantity = models.PositiveIntegerField()
    accepted_quantity = models.PositiveIntegerField()
    rejected_quantity = models.PositiveIntegerField()
    feed_back = models.TextField(blank=True)
    create_new_item = models.BooleanField(default=False)

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


class StoreInventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='inventory')
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, related_name='inventories', null=True)
    
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_allocated = models.PositiveIntegerField(default=0)
    quantity_qr_tagged = models.PositiveIntegerField(default=0)  # count of items with QR tags

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['store', 'batch',]]

    def __str__(self):
        return f'{self.store.code} - (Batch: {self.batch.batch_number})'
    
    
class TransferNote(models.Model):
    """Transfer  Note for moving items between stores"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Receipt'),
        ('RECEIVED', 'Recieved'),
        ('PARTIAL', 'Partially Received')
    ]

    transfer_note_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    transfer_date = models.DateField()

    from_store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='transfer_out'
    )

    to_store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name='transfer_in'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transfer_note_number}: {self.from_store.code} -> {self.to_store.code}'
    
class TransferNoteItem(models.Model):
    """Items in transfer note - Shows Exact batch and quantity"""
    transfer_note = models.ForeignKey(TransferNote, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    # Link to stock entries
    issue_entry = models.ForeignKey('StockEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_issue')
    receipt_entry = models.ForeignKey('StockEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_receipt')
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f'{self.transfer_note.transfer_note_number} - {self.item.code} ({self.quantity})'

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

class StockEntry(models.Model):
    ENTRY_TYPE = [
        ('RECEIPT', 'Receipt'),
        ('ISSUE', 'Issue'),
    ]
    entry_number = models.CharField(
        max_length=20, 
        default=generate_stock_entry_code,
        unique=True,
        editable=False)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    from_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, related_name='issued_entries')
    to_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, related_name='received_entries')
    from_inspection = models.ForeignKey(InspectionCertificate, on_delete=models.PROTECT, null=True)
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='location_entries')
    stock_register = models.ForeignKey(StockRegister, on_delete=models.PROTECT, related_name='entries')
    transfer_note = models.ForeignKey(TransferNote, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    balance = models.PositiveIntegerField(help_text='Enter balace')

    def __str__(self):
        return f'{self.entry_number} ({self.entry_type}) - {self.item.code} x {self.quantity}'

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
        related_name='batch'
    )

    item = models.ForeignKey(
        'Item', 
        on_delete=models.PROTECT
    )


    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE)
    source_store = models.ForeignKey(
        Store, 
        on_delete=models.PROTECT, 
        related_name='batches_created',
        help_text='Store that created/received this batch'
    )
    
    # Quantities
    total_quantity = models.PositiveIntegerField(
        help_text='Total quantity received in this batch'
    )
    current_quantity = models.PositiveIntegerField(
        help_text='Current quantity available (unassigned units)'
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

class AssetTag(models.Model):
    """Individual QR-tagged asset from a batch"""
    
    STATUS_CHOICES = [
        ('IN_STOCK', 'In Stock'),
        ('IN_USE', 'In Use'),
        ('UNDER_REPAIR', 'Under Repair'),
        ('WRITTEN_OFF', 'Written Off'),
        ('LOST', 'Lost'),
    ]

    # Core identifiers
    tag_number = models.CharField(max_length=100, unique=True, editable=False)
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    # Links to existing models
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, related_name='asset_tags')
    current_store = models.ForeignKey('Store', on_delete=models.PROTECT, related_name='current_assets')
    current_location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_assets')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_STOCK')
    assigned_to = models.CharField(max_length=255, blank=True)
    
    # Dates
    tagged_date = models.DateField(auto_now_add=True)
    
    # Additional info
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tag_number']),
            models.Index(fields=['qr_code_uuid']),
            models.Index(fields=['status', 'current_store']),
        ]

    def save(self, *args, **kwargs):
        if not self.tag_number:
            self.tag_number = self._generate_tag_number()
        
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new and not self.qr_code_image:
            self._generate_qr_code()
    
    def _generate_tag_number(self):
        """Generate unique tag: DEPT-ITEM-BATCH-0001"""
        dept = self.batch.item.department.code[:4].upper()
        item = self.batch.item.code[:6].upper()
        batch_seq = self.batch.batch_number.split('-')[-1][:4] if '-' in self.batch.batch_number else 'XXXX'
        
        # Get next sequence
        last_tag = AssetTag.objects.filter(batch=self.batch).order_by('-tag_number').first()
        next_seq = 1
        
        if last_tag and '-' in last_tag.tag_number:
            try:
                next_seq = int(last_tag.tag_number.split('-')[-1]) + 1
            except:
                pass
        
        return f"{dept}-{item}-{batch_seq}-{next_seq:04d}"
    
    def _generate_qr_code(self):
        """Generate QR code image with UUID"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        qr.add_data(str(self.qr_code_uuid))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_{self.tag_number}.png'
        
        self.qr_code_image.save(file_name, File(buffer), save=False)
        buffer.close()
        
        # Update without triggering save loop
        AssetTag.objects.filter(pk=self.pk).update(qr_code_image=self.qr_code_image)
    
    def get_full_details(self):
        """Get complete details including from batch and inspection"""
        batch = self.batch
        item = batch.item
        inspection = None
        
        if batch.inspection_item:
            inspection = batch.inspection_item.inspection
        
        return {
            'tag_number': self.tag_number,
            'qr_uuid': str(self.qr_code_uuid),
            'status': self.get_status_display(),
            'status_code': self.status,
            
            # Item details
            'item': {
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'specifications': item.specifications,
                'unit': item.unit,
                'category': item.category.name if item.category else None,
            },
            
            # Batch details
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'source_type': batch.get_source_type_display(),
                'warranty_expiry': batch.warranty_expiry_date,
                'manufacture_date': batch.manufacture_date,
                'batch_specifications': batch.batch_specifications,
            },
            
            # Inspection details (from batch)
            'inspection': {
                'certificate_number': inspection.certificate_number,
                'issued_on': inspection.issued_on,
                'contractor': inspection.contracter,
                'indenter': inspection.indenter,
                'consignee': inspection.consignee,
                'delivery_date': inspection.date_of_delivery,
                'delivery_status': inspection.get_delivery_status_display(),
            } if inspection else None,
            
            # Current location
            'current_store': {
                'id': self.current_store.id,
                'code': self.current_store.code,
                'name': self.current_store.name,
                'store_type': self.current_store.get_store_type_display(),
            },
            'current_location': {
                'id': self.current_location.id,
                'name': self.current_location.name,
                'code': self.current_location.code,
                'type': self.current_location.get_location_type_display(),
            } if self.current_location else None,
            
            # Assignment
            'assigned_to': self.assigned_to,
            'tagged_date': self.tagged_date,
            'remarks': self.remarks,
        }
    
    def __str__(self):
        return f"{self.tag_number} - {self.batch.item.name} ({self.get_status_display()})"





    
    



    