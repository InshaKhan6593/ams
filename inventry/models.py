from django.db import models
from django.db.models import Sum
from  django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid
from .helper_functions import *

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
    item_description = models.TextField()
    specifications = models.JSONField(default=dict)
    tendered_quantity = models.PositiveIntegerField()
    accepted_quantity = models.PositiveIntegerField()
    rejected_quantity = models.PositiveIntegerField()
    feed_back = models.TextField(blank=True)

    def __str__(self):
        return f'{self.item_description} - {self.inspection.certificate_number}'
    
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
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='inventories')
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_allocated =  models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['store', 'item']]

    def __str__(self):
        return f'{self.store.code} - {self.item.code}'
    
    
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
    stock_register = models.ForeignKey(StockRegister, on_delete=models.PROTECT)
    transfer_note = models.ForeignKey(TransferNote, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    balance = models.PositiveIntegerField(help_text='Enter balace')

    def __str__(self):
        return f'{self.entry_number} ({self.entry_type}) - {self.item.code} x {self.quantity}'
    

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.entry_type == 'RECEIPT':
            store, _  = StoreInventory.objects.get_or_create(
                store=self.to_store,
                item=self.item,
            )

            store.quantity_on_hand += self.quantity
            store.save()
        
        elif self.entry_type == 'ISSUE':
            store, _  = StoreInventory.objects.get_or_create(
                store=self.from_store,
                item=self.item,
            )

            store.quantity_allocated += self.quantity
            store.quantity_on_hand -= self.quantity



    





    
    



    