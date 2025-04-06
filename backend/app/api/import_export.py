from fastapi import APIRouter, UploadFile, File, HTTPException
import csv
from io import StringIO
from ..crud import create_item, create_container
from ..schemas import Item, Container

router = APIRouter()

@router.post("/api/import/items")
async def import_items(file: UploadFile = File(...)) -> Dict:
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    csv_file = StringIO(content.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    items_imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            item = Item(**row)
            if create_item(item):
                items_imported += 1
            else:
                errors.append({"row": row_num, "message": "Duplicate itemId"})
        except Exception as e:
            errors.append({"row": row_num, "message": str(e)})

    return {"success": True, "itemsImported": items_imported, "errors": errors}

@router.post("/api/import/containers")
async def import_containers(file: UploadFile = File(...)) -> Dict:
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    csv_file = StringIO(content.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    containers_imported = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            container = Container(**row)
            if create_container(container):
                containers_imported += 1
            else:
                errors.append({"row": row_num, "message": "Duplicate containerId"})
        except Exception as e:
            errors.append({"row": row_num, "message": str(e)})

    return {"success": True, "containersImported": containers_imported, "errors": errors}

@router.get("/api/export/arrangement")
async def export_arrangement():
    items = get_all_items()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item ID", "Container ID", "Coordinates (W1,D1,H1)", "Coordinates (W2,D2,H2)"])
    for item in items:
        writer.writerow([
            item["itemId"],
            item["containerId"],
            f"({item['startW']},{item['startD']},{item['startH']})",
            f"({item['endW']},{item['endD']},{item['endH']})"
        ])
    return {"content": output.getvalue(), "filename": "arrangement.csv"}