from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from rest_framework import viewsets
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv
from rest_framework import status
from django.db import transaction
from rest_framework.filters import SearchFilter, OrderingFilter
from .generator import *
import io
from django.conf import settings
from django.http import FileResponse

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department CRUD operations
    """
    queryset = Department.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DepartmentCreateUpdateSerializer
        return DepartmentDetailSerializer
    
    @action(detail=True, methods=['get'])
    def stores(self, request, pk=None):
        """Get all stores in this department"""
        department = self.get_object()
        stores = Store.objects.filter(department=department)
        serializer = StoreListSerializer(stores, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items in this department"""
        department = self.get_object()
        items = Item.objects.filter(department=department)
        serializer = ItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def locations(self, request, pk=None):
        """Get all locations in this department"""
        department = self.get_object()
        locations = Location.objects.filter(department=department)
        serializer = LocationListSerializer(locations, many=True)
        return Response(serializer.data)


# ============================================================================
# LOCATION VIEWSET
# ============================================================================

class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Location CRUD operations
    """
    queryset = Location.objects.select_related('department').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'location_type']
    search_fields = ['name', 'code', 'details']
    ordering_fields = ['name', 'code', 'location_type']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LocationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LocationCreateUpdateSerializer
        return LocationDetailSerializer


# ============================================================================
# ITEM CATEGORY VIEWSET
# ============================================================================

class ItemCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ItemCategory CRUD operations
    """
    queryset = ItemCategory.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ItemCategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ItemCategoryCreateUpdateSerializer
        return ItemCategoryDetailSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items in this category"""
        category = self.get_object()
        items = Item.objects.filter(category=category)
        serializer = ItemListSerializer(items, many=True)
        return Response(serializer.data)


# ============================================================================
# ITEM VIEWSET
# ============================================================================

class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Item CRUD operations
    """
    queryset = Item.objects.select_related('department', 'category', 'university_master_item').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'category', 'source_type', 'is_active']
    search_fields = ['name', 'code', 'specifications']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ItemListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ItemCreateUpdateSerializer
        return ItemDetailSerializer
    
    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """Get all batches of this item"""
        item = self.get_object()
        batches = Batch.objects.filter(item=item)
        serializer = BatchListSerializer(batches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory across all stores for this item"""
        item = self.get_object()
        batches = Batch.objects.filter(item=item)
        inventory = StoreInventory.objects.filter(batch__in=batches)
        serializer = StoreInventoryListSerializer(inventory, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stock_entries(self, request, pk=None):
        """Get all stock entries for this item"""
        item = self.get_object()
        entries = StockEntry.objects.filter(item=item).order_by('-created_at')
        serializer = StockEntryListSerializer(entries, many=True)
        return Response(serializer.data)


# ============================================================================
# STORE VIEWSET
# ============================================================================

class StoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Store CRUD operations
    """
    queryset = Store.objects.select_related('department', 'parent_store').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'store_type', 'parent_store']
    search_fields = ['name', 'code', 'incharge_name', 'location']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StoreListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StoreCreateUpdateSerializer
        return StoreDetailSerializer
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory for this store"""
        store = self.get_object()
        inventory = StoreInventory.objects.filter(store=store).select_related('batch', 'batch__item')
        serializer = StoreInventoryListSerializer(inventory, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def registers(self, request, pk=None):
        """Get all stock registers in this store"""
        store = self.get_object()
        registers = StockRegister.objects.filter(store=store)
        serializer = StockRegisterListSerializer(registers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """Get all batches in this store"""
        store = self.get_object()
        inventory = StoreInventory.objects.filter(store=store).select_related('batch')
        batches = [inv.batch for inv in inventory]
        serializer = BatchListSerializer(batches, many=True)
        return Response(serializer.data)


# ============================================================================
# STOCK REGISTER VIEWSET
# ============================================================================

class StockRegisterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StockRegister CRUD operations
    """
    queryset = StockRegister.objects.select_related('store').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['store', 'register_type', 'is_active']
    search_fields = ['register_name', 'register_number']
    ordering_fields = ['register_name', 'register_number', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StockRegisterListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StockRegisterCreateUpdateSerializer
        return StockRegisterDetailSerializer
    
    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """Get all entries in this register"""
        register = self.get_object()
        entries = StockEntry.objects.filter(stock_register=register).order_by('-created_at')
        serializer = StockEntryListSerializer(entries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get summary/report for this register"""
        register = self.get_object()
        entries = StockEntry.objects.filter(stock_register=register)
        
        summary = {
            'register': StockRegisterDetailSerializer(register).data,
            'total_entries': entries.count(),
            'total_receipts': entries.filter(entry_type='RECEIPT').count(),
            'total_issues': entries.filter(entry_type='ISSUE').count(),
            'total_adjustments': entries.filter(entry_type='ADJUSTMENT').count(),
        }
        return Response(summary)

    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        certificate = get_object_or_404(InspectionCertificate, pk=pk)
        items = certificate.items.select_related('item').all()

        if not items.exists():
            return HttpResponse("No items found for this inspection certificate.", status=404)

        # 🧾 Header / meta info
        data = {
            "contract_no": certificate.certificate_number,
            "date": certificate.issued_on.strftime("%Y-%m-%d") if certificate.issued_on else "",
            "contractor_name": certificate.contractor or "N/A",
            "contractor_address": "",
            "indenter": certificate.indenter or "N/A",
            "indent_no": certificate.certificate_number,
            "consignee": certificate.consignee or "N/A",
            "department": certificate.department.name if certificate.department else "N/A",
            "date_of_delivery": (
                certificate.date_of_delivery.strftime("%Y-%m-%d")
                if certificate.date_of_delivery else ""
            ),
            "delivery_status": certificate.get_delivery_status_display()
                if hasattr(certificate, "get_delivery_status_display") else "N/A",
            "date_of_inspection": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
            "stock_register_no": certificate.stock_register.register_name
                if certificate.stock_register else "N/A",
            "stock_page_nos": "",
            "stock_date_of_entry": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
            "dead_stock_register_no": "",
            "dead_stock_page_nos": "",
            "dead_stock_date_of_entry": "",
            "purchase_section_date": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
        }

        # 📦 Item details
        item_data = {
            "descriptions": [
                f"{i.item.name if i.item else 'N/A'} ({i.feedback or 'No remarks'})"
                for i in items
            ],
            "acct_unit": ["PCS"] * len(items),
            "t_quantity": [i.tendered_quantity or 0 for i in items],
            "r_quantity": [i.rejected_quantity or 0 for i in items],
            "a_quantity": [i.accepted_quantity or 0 for i in items],
        }

        # 🚫 Rejected items
        rejected_items = [i for i in items if (i.rejected_quantity or 0) > 0]
        rejected_item_data = {
            "item_no": [idx + 1 for idx, _ in enumerate(rejected_items)],
            "reasons": [i.feedback or "Not specified" for i in rejected_items],
        }

        # 🧠 File paths
        os.makedirs("media", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"InspectionCertificate_{certificate.certificate_number}_{timestamp}.pdf"
        pdf_path = os.path.join("media", pdf_filename)

        # 🔧 Clean up if file already exists
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        # 🧾 Generate the PDF using the generator class
        InspectionCertificateGenerator(
            logo_path=None,
            data=data,
            item_data=item_data,
            rejected_item_data=rejected_item_data
        )

        # 🔁 Move the generated file from temp name to media
        if os.path.exists("Inspection_Certificate.pdf"):
            os.rename("Inspection_Certificate.pdf", pdf_path)

        # ✅ Serve the generated PDF as a response
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{pdf_filename}"'
        return response
    
# INSPECTION CERTIFICATE VIEWSET
# ============================================================================

class InspectionCertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InspectionCertificate CRUD operations
    """
    queryset = InspectionCertificate.objects.select_related(
        'department', 'stock_register'
    ).prefetch_related('items').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'delivery_status', 'stock_register']
    search_fields = ['certificate_number', 'contractor', 'indenter', 'consignee']
    ordering_fields = ['certificate_number', 'issued_on', 'date_of_delivery', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InspectionCertificateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return InspectionCertificateCreateUpdateSerializer
        return InspectionCertificateDetailSerializer
    
    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """Get batches created from this inspection"""
        inspection = self.get_object()
        inspection_items = inspection.items.all()
        batches = Batch.objects.filter(inspection_item__in=inspection_items)
        serializer = BatchListSerializer(batches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process inspection certificate - create batches and stock entries"""
        from django.db import transaction
        from datetime import timedelta
        
        inspection = self.get_object()
        
        # Check if already processed
        if Batch.objects.filter(inspection_item__inspection=inspection).exists():
            return Response(
                {'error': 'Inspection certificate already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_batches = []
        created_entries = []
        
        try:
            with transaction.atomic():
                # Get the store from the stock register
                store = inspection.stock_register.store
                
                for inspection_item in inspection.items.all():
                    if inspection_item.accepted_quantity <= 0:
                        continue

                    batch_number = f"BATCH-{inspection.certificate_number}-{inspection_item.id}"

                    # Copy warranty data directly from inspection item
                    manufacture_date = inspection_item.manufacture_date
                    warranty_months = inspection_item.warranty_period_months
                    warranty_expiry = None

                    if manufacture_date and warranty_months:
                        from datetime import timedelta
                        warranty_expiry = manufacture_date + timedelta(days=warranty_months * 30)

                    # ✅ Create Batch (copy fields, don't calculate new)
                    batch = Batch.objects.create(
                        batch_number=batch_number,
                        inspection_item=inspection_item,
                        item=inspection_item.item,
                        source_type='DEPARTMENTAL_PURCHASE',
                        source_store=inspection.stock_register.store,
                        total_quantity=inspection_item.accepted_quantity,
                        current_quantity=inspection_item.accepted_quantity,
                        manufacture_date=manufacture_date,
                        warranty_period_months=warranty_months,
                        warranty_expiry_date=warranty_expiry,
                        remarks=f"Created from inspection {inspection.certificate_number}",
                        created_by=None  # or request.user if you later enable user tracking
                    )

                    created_batches.append(batch)
                    
                    # 2. Create or Update StoreInventory
                    inventory, created = StoreInventory.objects.get_or_create(
                        store=store,
                        batch=batch,
                        defaults={
                            'quantity_on_hand': inspection_item.accepted_quantity,
                            'quantity_allocated': 0,
                            'quantity_qr_tagged': 0
                        }
                    )
                    
                    if not created:
                        inventory.quantity_on_hand += inspection_item.accepted_quantity
                        inventory.save()
                    
                    # 3. Calculate balance (get last entry balance for this item in register)
                    last_entry = StockEntry.objects.filter(
                        stock_register=inspection.stock_register,
                        item=inspection_item.item
                    ).order_by('-created_at').first()
                    
                    previous_balance = last_entry.balance if last_entry else 0
                    new_balance = previous_balance + inspection_item.accepted_quantity
                    
                    # 4. Create StockEntry (RECEIPT type)
                    stock_entry = StockEntry.objects.create(
                        entry_type='RECEIPT',
                        item=inspection_item.item,
                        batch=batch,
                        quantity=inspection_item.accepted_quantity,
                        balance=new_balance,
                        store=store,
                        to_store=store,
                        inspection_certificate=inspection,
                        stock_register=inspection.stock_register,
                        remarks=f"Receipt from inspection certificate {inspection.certificate_number}"
                    )
                    created_entries.append(stock_entry)
                
                return Response({
                    'message': 'Inspection certificate processed successfully',
                    'inspection_id': inspection.id,
                    'batches_created': len(created_batches),
                    'entries_created': len(created_entries),
                    'batches': BatchListSerializer(created_batches, many=True).data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error processing inspection: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        certificate = get_object_or_404(InspectionCertificate, pk=pk)
        items = certificate.items.select_related('item').all()
        if not items.exists():
            return HttpResponse("No items found for this inspection certificate.", status=404)
        
        # 🧾 Header / meta info
        data = {
            "contract_no": certificate.certificate_number,
            "date": certificate.issued_on.strftime("%Y-%m-%d") if certificate.issued_on else "",
            "contractor_name": certificate.contractor or "N/A",
            "contractor_address": "",
            "indenter": certificate.indenter or "N/A",
            "indent_no": certificate.certificate_number,
            "consignee": certificate.consignee or "N/A",
            "department": certificate.department.name if certificate.department else "N/A",
            "date_of_delivery": (
                certificate.date_of_delivery.strftime("%Y-%m-%d")
                if certificate.date_of_delivery else ""
            ),
            "delivery_status": (
                certificate.get_delivery_status_display()
                if hasattr(certificate, "get_delivery_status_display")
                else "N/A"
            ),
            "date_of_inspection": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
            "stock_register_no": certificate.stock_register.register_name
                if certificate.stock_register else "N/A",
            "stock_page_nos": "",
            "stock_date_of_entry": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
            "dead_stock_register_no": "",
            "dead_stock_page_nos": "",
            "dead_stock_date_of_entry": "",
            "purchase_section_date": certificate.issued_on.strftime("%Y-%m-%d")
                if certificate.issued_on else "",
        }
        
        # 📦 Item details
        item_data = {
            "descriptions": [
                f"{i.item.name if i.item else 'N/A'} ({i.feedback or 'No remarks'})"
                for i in items
            ],
            "acct_unit": ["PCS"] * len(items),
            "t_quantity": [i.tendered_quantity or 0 for i in items],
            "r_quantity": [i.rejected_quantity or 0 for i in items],
            "a_quantity": [i.accepted_quantity or 0 for i in items],
        }
        
        # 🚫 Rejected items
        rejected_items = [i for i in items if (i.rejected_quantity or 0) > 0]
        rejected_item_data = {
            "item_no": [idx + 1 for idx, _ in enumerate(rejected_items)],
            "reasons": [i.feedback or "Not specified" for i in rejected_items],
        }
        
        # 🧠 File paths - use Django's MEDIA_ROOT
        from django.conf import settings
        media_dir = settings.MEDIA_ROOT
        os.makedirs(media_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"InspectionCertificate_{certificate.certificate_number}_{timestamp}.pdf"
        pdf_path = os.path.join(media_dir, pdf_filename)
        
        # 🧾 Generate PDF - the generator creates the file in __init__
        # It generates a file named "Inspection_Certificate_{contract_no}.pdf" in the current directory
        generator = InspectionCertificateGenerator(
            logo_path=None,
            data=data,
            item_data=item_data,
            rejected_item_data=rejected_item_data
        )
        
        # 🪶 Move the generated file to media folder
        generated_filename = f"Inspection_Certificate_{certificate.certificate_number}.pdf"
        if os.path.exists(generated_filename):
            # Move the file to media directory with timestamp
            os.rename(generated_filename, pdf_path)
        else:
            return HttpResponse("PDF generation failed.", status=500)
        
        # ✅ Serve file back as HTTP response
        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            
            response = HttpResponse(pdf_data, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="{pdf_filename}"'
            
            return response
        except Exception as e:
            return HttpResponse(f"Error serving PDF: {str(e)}", status=500)
# ============================================================================
# INSPECTION ITEM VIEWSET (Nested under Inspection Certificate)
# ============================================================================

class InspectionItemViewSet(viewsets.ModelViewSet):
    """
    Nested ViewSet for InspectionItem under InspectionCertificate
    """
    serializer_class = InspectionItemSerializer
    
    def get_queryset(self):
        inspection_id = self.kwargs.get('inspection_pk')
        return InspectionItem.objects.filter(inspection_id=inspection_id)
    
    def perform_create(self, serializer):
        inspection_id = self.kwargs.get('inspection_pk')
        serializer.save(inspection_id=inspection_id)


# ============================================================================
# BATCH VIEWSET
# ============================================================================

class BatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Batch CRUD operations
    """
    queryset = Batch.objects.select_related(
        'item', 'source_store', 'inspection_item', 'transfer_item'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['item', 'source_store', 'source_type', 'is_active']
    search_fields = ['batch_number', 'remarks']
    ordering_fields = ['batch_number', 'created_at', 'expiry_date']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BatchListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BatchCreateUpdateSerializer
        return BatchDetailSerializer
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory across stores for this batch"""
        batch = self.get_object()
        inventory = StoreInventory.objects.filter(batch=batch).select_related('store')
        serializer = StoreInventoryListSerializer(inventory, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transfers(self, request, pk=None):
        """Get all transfers involving this batch"""
        batch = self.get_object()
        # TODO: Implement when TransferNoteItem is ready
        return Response({'message': 'Transfer history for batch'})


# ============================================================================
# STORE INVENTORY VIEWSET
# ============================================================================

class StoreInventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for StoreInventory - Read only, updated through transactions
    """
    queryset = StoreInventory.objects.select_related(
        'store', 'batch', 'batch__item'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['store', 'batch']
    ordering_fields = ['last_updated', 'quantity_on_hand']
    ordering = ['-last_updated']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StoreInventoryListSerializer
        return StoreInventoryDetailSerializer
    
    @action(detail=False, methods=['get'])
    def by_store(self, request):
        """Get inventory for a specific store"""
        store_id = request.query_params.get('store_id')
        if not store_id:
            return Response(
                {'error': 'store_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory = self.get_queryset().filter(store_id=store_id)
        serializer = self.get_serializer(inventory, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get inventory for a specific batch"""
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response(
                {'error': 'batch_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory = self.get_queryset().filter(batch_id=batch_id)
        serializer = self.get_serializer(inventory, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get items with low stock (quantity <= 10)"""
        inventory = self.get_queryset().filter(quantity_on_hand__lte=10)
        serializer = self.get_serializer(inventory, many=True)
        return Response(serializer.data)


# ============================================================================
# STOCK ENTRY VIEWSET
# ============================================================================

class StockEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StockEntry - Mostly read-only, created through transactions
    Manual adjustments allowed
    """
    queryset = StockEntry.objects.select_related(
        'item', 'batch', 'store', 'from_store', 'to_store', 
        'to_location', 'stock_register'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entry_type', 'item', 'batch', 'store', 'stock_register']
    search_fields = ['entry_number', 'remarks']
    ordering_fields = ['entry_date', 'created_at', 'entry_number']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StockEntryListSerializer
        elif self.action in ['create']:
            return StockEntryCreateSerializer
        return StockEntryDetailSerializer
    
    # Override to allow only GET and POST (for adjustments)
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = []  # Deny these actions
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def by_store(self, request):
        """Get entries for specific store"""
        store_id = request.query_params.get('store_id')
        if not store_id:
            return Response(
                {'error': 'store_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entries = self.get_queryset().filter(store_id=store_id)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get entries for specific item"""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entries = self.get_queryset().filter(item_id=item_id)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get entries for specific batch"""
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response(
                {'error': 'batch_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entries = self.get_queryset().filter(batch_id=batch_id)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def adjustment(self, request):
        """Create adjustment entry"""
        serializer = StockEntryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(entry_type='ADJUSTMENT')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        """Create reversing adjustment entry"""
        original_entry = self.get_object()
        
        # Create reverse entry
        reverse_data = {
            'entry_type': 'ADJUSTMENT',
            'item': original_entry.item.id,
            'batch': original_entry.batch.id if original_entry.batch else None,
            'quantity': -original_entry.quantity,
            'balance': original_entry.balance - original_entry.quantity,
            'store': original_entry.store.id,
            'stock_register': original_entry.stock_register.id,
            'reference_entry': original_entry.id,
            'adjustment_reason': f'Reversal of entry {original_entry.entry_number}',
            'remarks': request.data.get('remarks', '')
        }
        
        serializer = StockEntryCreateSerializer(data=reverse_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TransferNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TransferNote CRUD operations
    """
    queryset = TransferNote.objects.select_related(
        'from_store', 'to_store', 'to_location',
    ).prefetch_related('items').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['from_store', 'to_store', 'to_location', 'status',]
    search_fields = ['transfer_note_number', 'remarks']
    ordering_fields = ['transfer_date', 'created_at', 'transfer_note_number']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TransferNoteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TransferNoteCreateUpdateSerializer
        elif self.action == 'acknowledge':
            return TransferNoteAcknowledgmentSerializer
        return TransferNoteDetailSerializer
    
    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """Issue transfer note - create issue entries and update inventory"""
        from django.db import transaction
        
        transfer_note = self.get_object()
        
        if transfer_note.status != 'ISSUED':
            return Response(
                {'error': 'Only issued transfer notes can be issued'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                for transfer_item in transfer_note.items.all():
                    # 1. Check inventory availability
                    inventory = StoreInventory.objects.filter(
                        store=transfer_note.from_store,
                        batch=transfer_item.batch
                    ).first()
                    
                    if not inventory or inventory.quantity_on_hand < transfer_item.quantity_sent:
                        raise ValueError(
                            f"Insufficient inventory for batch {transfer_item.batch.batch_number}"
                        )
                    
                    # 2. Update source store inventory
                    inventory.quantity_on_hand -= transfer_item.quantity_sent
                    inventory.quantity_allocated+= transfer_item.quantity_sent
                    inventory.save()
                    
                    # 3. Update batch current quantity
                    transfer_item.batch.current_quantity -= transfer_item.quantity_sent
                    transfer_item.batch.save()
                    
                    # 4. Get stock register for from_store
                    stock_register = StockRegister.objects.filter(
                        store=transfer_note.from_store
                    ).first()
                    
                    if not stock_register:
                        raise ValueError(f"No stock register found for store {transfer_note.from_store.name}")
                    
                    # 5. Calculate balance
                    last_entry = StockEntry.objects.filter(
                        stock_register=stock_register,
                        item=transfer_item.item
                    ).order_by('-created_at').first()
                    
                    previous_balance = last_entry.balance if last_entry else 0
                    new_balance = previous_balance - transfer_item.quantity_sent
                    
                    # 6. Create Issue StockEntry
                    issue_entry = StockEntry.objects.create(
                        entry_type='ISSUE',
                        item=transfer_item.item,
                        batch=transfer_item.batch,
                        quantity=-transfer_item.quantity_sent,  # Negative for issue
                        balance=new_balance,
                        store=transfer_note.from_store,
                        from_store=transfer_note.from_store,
                        to_store=transfer_note.to_store,
                        to_location=transfer_note.to_location,
                        stock_register=stock_register,
                        transfer_note=transfer_note,
                        transfer_note_item=transfer_item,
                        remarks=f"Issue via transfer note {transfer_note.transfer_note_number}"
                    )
                    
                    # Link to transfer item
                    transfer_item.issue_entry = issue_entry
                    transfer_item.save()
                
                # Update transfer note status
                transfer_note.status = 'ISSUED'
                transfer_note.save()
                
                return Response({
                    'message': 'Transfer note issued successfully',
                    'transfer_note_id': transfer_note.id,
                    'transfer_note_number': transfer_note.transfer_note_number
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error issuing transfer: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def acknowledge_and_stock(self, request, pk=None):
        transfer_note = self.get_object()
        serializer = TransferNoteAcknowledgmentSerializer(
            data=request.data, 
            context={'transfer_note': transfer_note, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'Acknowledged and stock updated'})
    
class TransferNoteItemViewSet(viewsets.ModelViewSet):
    """
    Nested ViewSet for TransferNoteItem under TransferNote
    """
    serializer_class = TransferNoteItemSerializer
    
    def get_queryset(self):
        transfer_note_id = self.kwargs.get('transfernote_pk')
        return TransferNoteItem.objects.filter(transfer_note_id=transfer_note_id)
    
    def perform_create(self, serializer):
        transfer_note_id = self.kwargs.get('transfernote_pk')
        serializer.save(transfer_note_id=transfer_note_id)
    
    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        """Create reversing adjustment entry"""
        original_entry = self.get_object()
        
        # Create reverse entry
        reverse_data = {
            'entry_type': 'ADJUSTMENT',
            'item': original_entry.item.id,
            'batch': original_entry.batch.id if original_entry.batch else None,
            'quantity': -original_entry.quantity,
            'balance': original_entry.balance - original_entry.quantity,
            'store': original_entry.store.id,
            'stock_register': original_entry.stock_register.id,
            'reference_entry': original_entry.id,
            'adjustment_reason': f'Reversal of entry {original_entry.entry_number}',
            'remarks': request.data.get('remarks', '')
        }
        
        serializer = StockEntryCreateSerializer(data=reverse_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RequisitionViewSet(viewsets.ModelViewSet):
    queryset = Requisition.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return RequisitionCreateSerializer
        return RequisitionSerializer
    
    @action(detail=True, methods=['post'], url_path='process-items')
    def process_items(self, request, pk=None):
        """
        Process requisition items:
        - Set provided_quantity
        - Set rejection if provided_quantity is 0
        - Assign main_stock_register
        - Assign batch if batch_id is provided
        - Only validate quantities, do NOT update inventory or stock entries
        """
        requisition = self.get_object()
        serializer = RequisitionItemProcessSerializer(
            data=request.data.get('items', []),
            many=True
        )
        serializer.is_valid(raise_exception=True)

        for item_data in serializer.validated_data:
            try:
                item = requisition.items.get(id=item_data['id'])

                # Update provided quantity and rejection
                item.provided_quantity = item_data['provided_quantity']
                if item_data['provided_quantity'] == 0:
                    item.is_rejected = True
                    item.reject_reason = item_data.get('reject_reason', '')
                else:
                    item.is_rejected = False
                    item.reject_reason = ''

                # Assign main stock register
                stock_register = StockRegister.objects.get(id=item_data['main_stock_register'])
                item.main_stock_register = stock_register

                # Assign batch if provided
                batch_id = item_data.get('batch_id')
                if batch_id:
                    batch = Batch.objects.get(id=batch_id)
                    item.batch = batch

                    # Validate that provided_quantity does not exceed batch current_quantity
                    if item_data['provided_quantity'] > batch.current_quantity:
                        raise serializers.ValidationError(
                            f"Provided quantity ({item_data['provided_quantity']}) exceeds available batch quantity ({batch.current_quantity}) for item {item.item_name}."
                        )

                item.save()
            except RequisitionItem.DoesNotExist:
                continue

        return Response(RequisitionSerializer(requisition).data)
    
    @action(detail=True, methods=['post'], url_path='make-transit')
    def make_transit(self, request, pk=None):
        """
        Marks the requisition as IN_TRANSIT.
        Deducts provided_quantity from batch in main store inventory,
        increments allocated quantity, and creates StockEntry for each item.
        """
        requisition = self.get_object()

        if requisition.status != 'APPROVED':
            return Response(
                {"detail": "Only approved requisitions can be moved to IN_TRANSIT."},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in requisition.items.all():
            if item.provided_quantity <= 0 or item.is_rejected:
                continue  # Skip rejected or zero-provided items

            if not item.batch or not item.main_stock_register:
                return Response(
                    {"detail": f"Item {item.item_name} is missing batch or stock register assignment."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Fetch StoreInventory for main store and batch
                store_inventory = StoreInventory.objects.get(
                    store=requisition.main_store,
                    batch=item.batch
                )
            except StoreInventory.DoesNotExist:
                return Response(
                    {"detail": f"No store inventory found for item {item.item_name} in main store."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if store_inventory.quantity_on_hand < item.provided_quantity:
                return Response(
                    {"detail": f"Not enough stock in main store for {item.item_name}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update inventory: deduct on-hand and increment allocated
            store_inventory.quantity_on_hand -= item.provided_quantity
            store_inventory.quantity_allocated += item.provided_quantity
            store_inventory.save()

            # Create StockEntry for this issue
            current_balance = store_inventory.quantity_on_hand
            StockEntry.objects.create(
                entry_type='ISSUE',
                item=item.batch.item,
                batch=item.batch,
                quantity=-item.provided_quantity,
                balance=current_balance,
                store=requisition.main_store,
                stock_register=item.main_stock_register,
                remarks=f"Issued for Requisition {requisition.requisition_no}",
                created_by=request.user if request.user.is_authenticated else None
            )

        # Mark requisition as IN_TRANSIT
        requisition.status = 'IN_TRANSIT'
        requisition.save()

        return Response(RequisitionSerializer(requisition).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['POST'])
    def acknowledge(self, request, pk=None):
        """
        Called by the receiving store to mark requisition as RECEIVED
        """
        requisition = self.get_object()

        # Optional: check that request.user belongs to the receiving store
        # if requisition.main_store not linked to user:
        #     return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        requisition.mark_as_received(None)
        serializer = self.get_serializer(requisition)
        return Response(serializer.data, status=status.HTTP_200_OK)