import csv
import io

from django.db import transaction

from apps.customers.serializers.customer_serializer import CustomerSerializer
from mo.celery import celery_app


@celery_app.task(name="import_customers_task", bind=True)
def import_customers_task(self, raw_content):
    """
    Background task that reads lines 'external_id,score',
    crea cada Customer y retorna un resumen.
    """
    reader = csv.reader(io.StringIO(raw_content))
    created, errors = [], []

    with transaction.atomic():
        for idx, row in enumerate(reader, start=1):
            if len(row) != 2:
                errors.append(f"Line {idx}: expected 2 values, got {len(row)}")
                continue

            ext_id, score = row[0].strip(), row[1].strip()
            ser = CustomerSerializer(data={"external_id": ext_id, "score": score})
            if ser.is_valid():
                ser.save()
                created.append(ext_id)
            else:
                errors.append({f"Line {idx}": ser.errors})

    return {"created": created, "errors": errors}
