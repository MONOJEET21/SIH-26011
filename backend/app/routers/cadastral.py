from fastapi import APIRouter, HTTPException

from ml.gis.query.cadastral_queries import CadastralQueryEngine


router = APIRouter(
    prefix="/api",
    tags=["cadastral"],
)

engine = CadastralQueryEngine()


def _result_or_404(result, description: str):
    if not result.success:
        raise HTTPException(
            status_code=404,
            detail=result.error or f"{description} not found",
        )

    response = result.to_dict()

    # Ensure collection responses expose the IDs
    # of the returned entities themselves.
    if isinstance(response.get("data"), list):
        data = response["data"]

        if data and "unit_id" in data[0]:
            response["entity_ids"] = [
                item["unit_id"]
                for item in data
                if "unit_id" in item
            ]

        elif data and "building_id" in data[0]:
            response["entity_ids"] = [
                item["building_id"]
                for item in data
                if "building_id" in item
            ]

        elif data and "floor_id" in data[0]:
            response["entity_ids"] = [
                item["floor_id"]
                for item in data
                if "floor_id" in item
            ]

        elif data and "asset_id" in data[0]:
            response["entity_ids"] = [
                item["asset_id"]
                for item in data
                if "asset_id" in item
            ]

    return response


@router.get("/parcels/{parcel_id}")
def get_parcel(parcel_id: str):
    return _result_or_404(
        engine.get_parcel(parcel_id),
        f"Parcel '{parcel_id}'",
    )


@router.get("/buildings/{building_id}")
def get_building(building_id: str):
    return _result_or_404(
        engine.get_building(building_id),
        f"Building '{building_id}'",
    )


@router.get("/buildings/{building_id}/floors/{floor_id}")
def get_floor(building_id: str, floor_id: str):
    return _result_or_404(
        engine.get_floor(building_id, floor_id),
        f"Floor '{floor_id}'",
    )


@router.get("/property-units/{unit_id}")
def get_property_unit(unit_id: str):
    return _result_or_404(
        engine.get_property_unit(unit_id),
        f"Property unit '{unit_id}'",
    )


@router.get("/parcels/{parcel_id}/property-units")
def get_units_in_parcel(parcel_id: str):
    return _result_or_404(
        engine.get_units_in_parcel(parcel_id),
        f"Property units in parcel '{parcel_id}'",
    )


@router.get("/buildings/{building_id}/property-units")
def get_units_in_building(building_id: str):
    return _result_or_404(
        engine.get_units_in_building(building_id),
        f"Property units in building '{building_id}'",
    )


@router.get(
    "/buildings/{building_id}/floors/{floor_id}/property-units"
)
def get_units_on_floor(building_id: str, floor_id: str):
    return _result_or_404(
        engine.get_units_on_floor(building_id, floor_id),
        f"Property units on floor '{floor_id}'",
    )


@router.get("/parcels/{parcel_id}/underground-assets")
def get_underground_assets(parcel_id: str):
    return _result_or_404(
        engine.get_underground_assets(parcel_id),
        f"Underground assets in parcel '{parcel_id}'",
    )


@router.get("/parcels/{parcel_id}/entities")
def find_entities_in_parcel(parcel_id: str):
    return _result_or_404(
        engine.find_entities_in_parcel(parcel_id),
        f"Entities in parcel '{parcel_id}'",
    )


@router.get("/parcels/{parcel_id}/above")
def find_entities_above_parcel(parcel_id: str):
    return _result_or_404(
        engine.find_entities_above_parcel(parcel_id),
        f"Entities above parcel '{parcel_id}'",
    )


@router.get("/parcels/{parcel_id}/underground")
def find_underground_assets_below(parcel_id: str):
    return _result_or_404(
        engine.find_underground_assets_below(parcel_id),
        f"Underground entities below parcel '{parcel_id}'",
    )


@router.get("/statistics")
def get_statistics():
    result = engine.get_statistics()

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "Unable to retrieve statistics",
        )

    return result.to_dict()


@router.get("/schema")
def get_schema():
    result = engine.get_schema()

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "Unable to retrieve schema",
        )

    return result.to_dict()