import uuid
import random
import string
from django.utils import timezone
from datetime import datetime
from django.utils.text import slugify
from django.apps import apps

def generate_stock_entry_code():
    date_part = timezone.now().strftime("%y%m%d")  # e.g. 251030
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SR-{date_part}-{random_part}"


def generate_department_code(name: str) -> str:
    """
    Generate unique short code for Department
    e.g. 'Computer Science' -> 'CSD-01'
    """
    Department = apps.get_model('inventry', 'Department')  # dynamically get model
    base_code = ''.join(word[0].upper() for word in name.split())[:3]
    existing_codes = Department.objects.filter(code__startswith=base_code).count()
    return f"{base_code}-{existing_codes + 1:02d}"


def generate_register_number(store_code: str, register_type: str) -> str:
    """
    Generate unique, meaningful Stock Register code.
    Example: MAIN-DSR-001, SUB-CON-002, etc.
    """
    StockRegister = apps.get_model('inventry', 'StockRegister')

    type_map = {
        'DEADSTOCK': 'DSR',
        'CONSUMABLE': 'CON',
        'EQUIPMENT': 'EQT'
    }

    type_code = type_map.get(register_type, 'REG')
    count = StockRegister.objects.filter(
        register_type=register_type,
        store__code=store_code
    ).count()

    return f"{store_code.upper()}-{type_code}-{count + 1:03d}"