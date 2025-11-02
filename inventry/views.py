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
from rest_framework import status
from rest_framework.permissions import AllowAny

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
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ListStoreInventrySerializer
        return StoreInventrySerializer

    def get_serializer_context(self):
        return {'store_id': self.kwargs['store_pk']}
    
    def get_queryset(self):
        store_pk = self.kwargs.get('store_pk')
        return StoreInventory.objects.filter(
            store_id=store_pk
        ).select_related('batch', 'batch__item', 'store')
    
    @action(detail=True, methods=['post'])
    def generate_tags(self, request, store_pk=None, pk=None):
        inventory = self.get_object()

        # Use serializer to validate input
        serializer = GenerateQRTagsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        # Check available quantity
        available = inventory.quantity_on_hand - inventory.quantity_qr_tagged
        if quantity > available:
            return Response({
                'error': f'Only {available} untagged items available',
                'details': {
                    'quantity_on_hand': inventory.quantity_on_hand,
                    'already_tagged': inventory.quantity_qr_tagged,
                    'available': available
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tags_created = []
        try:
            with transaction.atomic():
                for _ in range(quantity):
                    tag = AssetTag.objects.create(
                        batch=inventory.batch,
                        current_store=inventory.store,
                        created_by=request.user if request.user.is_authenticated else None
                    )
                    tags_created.append({
                        'id': tag.id,
                        'tag_number': tag.tag_number,
                        'qr_uuid': str(tag.qr_code_uuid),
                        'qr_image_url': request.build_absolute_uri(tag.qr_code_image.url) if tag.qr_code_image else None
                    })
                
                # Update inventory
                inventory.quantity_qr_tagged += quantity
                inventory.save()
            
            # Generate print URL
            tag_ids = ','.join(str(t['id']) for t in tags_created)
            print_url = request.build_absolute_uri(
                f'/api/stores/{store_pk}/inventries/{pk}/print_tags/?ids={tag_ids}'
            )
            
            return Response({
                'success': True,
                'message': f'{quantity} QR tags generated successfully',
                'tags': tags_created,
                'inventory': {
                    'batch_number': inventory.batch.batch_number,
                    'item_name': inventory.batch.item.name,
                    'quantity_on_hand': inventory.quantity_on_hand,
                    'quantity_qr_tagged': inventory.quantity_qr_tagged,
                    'untagged_remaining': inventory.quantity_on_hand - inventory.quantity_qr_tagged
                },
                'print_url': print_url
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Failed to generate tags: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def print_tags(self, request, store_pk=None, pk=None):
        """
        Generate printable QR labels
        GET /api/stores/{store_id}/inventries/{id}/print_tags/?ids=1,2,3
        """
        inventory = self.get_object()
        tag_ids = request.query_params.get('ids', '').split(',')
        
        if not tag_ids or tag_ids == ['']:
            # Print all tags for this inventory
            tags = AssetTag.objects.filter(
                batch=inventory.batch,
                current_store=inventory.store
            )
        else:
            tags = AssetTag.objects.filter(id__in=tag_ids)
        
        tags = tags.select_related('batch__item', 'current_store')
        
        if not tags.exists():
            return HttpResponse('<h1>No tags found</h1>')
        
        # Generate HTML for printing
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QR Code Labels</title>
    <style>
        @page {{
            size: A4;
            margin: 10mm;
        }}
        
        @media print {{
            .label {{
                page-break-inside: avoid;
            }}
            .no-print {{
                display: none;
            }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        
        .no-print {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 5px;
        }}
        
        .no-print button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }}
        
        .no-print button:hover {{
            background: #0056b3;
        }}
        
        .container {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: flex-start;
        }}
        
        .label {{
            width: 8cm;
            height: 5cm;
            border: 2px solid #000;
            padding: 10px;
            box-sizing: border-box;
            display: inline-flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        
        .qr-code {{
            text-align: center;
            flex-grow: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .qr-code img {{
            max-width: 120px;
            max-height: 120px;
            width: auto;
            height: auto;
        }}
        
        .info {{
            font-size: 11px;
            margin-top: 5px;
            border-top: 1px solid #ccc;
            padding-top: 5px;
        }}
        
        .tag-number {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 3px;
        }}
        
        .item-name {{
            font-size: 12px;
            margin-bottom: 2px;
        }}
        
        .batch-store {{
            font-size: 10px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <button onclick="window.print()">🖨️ Print Labels</button>
        <p><strong>Total Labels:</strong> {tags.count()}</p>
        <p><strong>Batch:</strong> {inventory.batch.batch_number}</p>
        <p><strong>Item:</strong> {inventory.batch.item.name}</p>
    </div>
    
    <div class="container">
'''
        
        for tag in tags:
            qr_url = request.build_absolute_uri(tag.qr_code_image.url) if tag.qr_code_image else ''
            
            html += f'''
        <div class="label">
            <div class="qr-code">
                <img src="{qr_url}" alt="QR Code" />
            </div>
            <div class="info">
                <div class="tag-number">{tag.tag_number}</div>
                <div class="item-name">{tag.batch.item.name}</div>
                <div class="batch-store">
                    Batch: {tag.batch.batch_number} | Store: {tag.current_store.code}
                </div>
            </div>
        </div>
'''
        
        html += '''
    </div>
</body>
</html>
'''
        
        return HttpResponse(html, content_type='text/html')
    
    @action(detail=True, methods=['get'])
    def tagged_assets(self, request, store_pk=None, pk=None):
        """
        View all tagged assets for this inventory
        GET /api/stores/{store_id}/inventries/{id}/tagged_assets/
        """
        inventory = self.get_object()
        
        assets = AssetTag.objects.filter(
            batch=inventory.batch,
            current_store=inventory.store
        ).select_related('current_location')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            assets = assets.filter(status=status_filter)
        
        # Summary
        summary = {
            'total': assets.count(),
            'by_status': {}
        }
        
        for status_code, status_label in AssetTag.STATUS_CHOICES:
            count = assets.filter(status=status_code).count()
            if count > 0:
                summary['by_status'][status_label] = count
        
        # Asset list
        assets_data = []
        for asset in assets:
            assets_data.append({
                'id': asset.id,
                'tag_number': asset.tag_number,
                'qr_uuid': str(asset.qr_code_uuid),
                'status': asset.get_status_display(),
                'status_code': asset.status,
                'location': asset.current_location.name if asset.current_location else None,
                'assigned_to': asset.assigned_to,
                'tagged_date': asset.tagged_date,
            })
        
        return Response({
            'inventory': {
                'batch_number': inventory.batch.batch_number,
                'item_name': inventory.batch.item.name,
                'item_code': inventory.batch.item.code,
                'quantity_on_hand': inventory.quantity_on_hand,
                'quantity_tagged': inventory.quantity_qr_tagged,
                'untagged': inventory.quantity_on_hand - inventory.quantity_qr_tagged,
            },
            'summary': summary,
            'assets': assets_data
        })
    
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
    
class AssetTagViewSet(ModelViewSet):
    """ViewSet for QR Tagged Assets"""
    queryset = AssetTag.objects.all().select_related(
        'batch__item__department',
        'batch__item__category',
        'current_store',
        'current_location'
    )
    permission_classes = [AllowAny]  # No login required
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AssetTagDetailSerializer
        elif self.action in ['create']:
            return AssetTagCreateSerializer
        elif self.action in ['update', 'partial_update', 'update_status']:
            return AssetTagUpdateSerializer
        return AssetTagListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filters
        status_filter = self.request.query_params.get('status')
        store_id = self.request.query_params.get('store')
        batch_id = self.request.query_params.get('batch')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if store_id:
            queryset = queryset.filter(current_store_id=store_id)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        if search:
            queryset = queryset.filter(
                tag_number__icontains=search
            ) | queryset.filter(
                batch__item__name__icontains=search
            )
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='scan/(?P<uuid>[^/.]+)')
    def scan(self, request, uuid=None):
        """
        Scan QR code by UUID
        GET /api/asset-tags/scan/{uuid}/
        """
        try:
            asset = AssetTag.objects.select_related(
                'batch__item__department',
                'batch__item__category',
                'batch__inspection_item__inspection',
                'current_store',
                'current_location'
            ).get(qr_code_uuid=uuid)
            
            return Response({
                'success': True,
                'data': asset.get_full_details()
            })
        except AssetTag.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Asset not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update asset status and location
        POST /api/asset-tags/{id}/update_status/
        Body: {
            "status": "IN_USE",
            "assigned_to": "AV Hall",
            "location_id": 10,
            "remarks": "Installed in auditorium"
        }
        """
        asset = self.get_object()
        
        # Update status
        new_status = request.data.get('status')
        if new_status:
            asset.status = new_status
        
        # Update assignment
        assigned_to = request.data.get('assigned_to')
        if assigned_to:
            asset.assigned_to = assigned_to
        
        # Update location
        location_id = request.data.get('location_id')
        if location_id:
            asset.current_location_id = location_id
        
        # Update store if provided
        store_id = request.data.get('store_id')
        if store_id:
            asset.current_store_id = store_id
        
        # Add remarks
        new_remarks = request.data.get('remarks', '')
        if new_remarks:
            asset.remarks = f"{asset.remarks}\n{new_remarks}".strip()
        
        asset.save()
        
        serializer = AssetTagDetailSerializer(asset, context={'request': request})
        return Response({
            'success': True,
            'message': f'Asset status updated to {asset.get_status_display()}',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def status_choices(self, request):
        """
        Get available status choices
        GET /api/asset-tags/status_choices/
        """
        return Response({
            'choices': [
                {'value': code, 'label': label}
                for code, label in AssetTag.STATUS_CHOICES
            ]
        })
    


    
