import csv
import io

from django.db import transaction
from apps.customers.serializers.customer_serializer import CustomerSerializer
from mo.celery import celery_app


@celery_app.task(name="import_customers_task", bind=True)
def import_customers_task(self, raw_content):
    """
    Background task that reads lines in format:
    external_id,score[,preapproved_at]
    
    - Creates each Customer using the validated serializer
    - Returns a summary with created and errors
    """
    reader = csv.reader(io.StringIO(raw_content))
    created, errors = [], []

    with transaction.atomic():
        for idx, row in enumerate(reader, start=1):
            if len(row) < 2 or len(row) > 3:
                errors.append(f"Line {idx}: expected 2 to 4 values, got {len(row)}")
                continue

            data = {
                "external_id": row[0].strip(),
                "score": row[1].strip()
            }

            if len(row) >= 3 and row[2].strip():
                data["preapproved_at"] = row[2].strip()

            ser = CustomerSerializer(data=data)
            if ser.is_valid():
                ser.save()
                created.append(data["external_id"])
            else:
                errors.append({f"Line {idx}": ser.errors})

    return {"created": created, "errors": errors}
