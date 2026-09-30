import { useEffect, useRef, useState } from "react";
  import type { KeyboardEvent } from "react";
  import { Viewer } from "resium";
  import {
    Cartesian3,
    Color,
    Ion,
    Viewer as CesiumViewer,
    GeoJsonDataSource as CesiumGeoJsonDataSource,
    CustomDataSource,
    PropertyBag,
    ScreenSpaceEventHandler,
    ScreenSpaceEventType,
    ConstantProperty,
    ColorMaterialProperty,
    HeadingPitchRange,
    defined,
  } from "cesium";

  import "cesium/Build/Cesium/Widgets/widgets.css";
  import "./App.css";

  type LayerKey =
    | "parcels"
    | "buildings"
    | "floors"
    | "propertyUnits"
    | "underground";

  type DataMode = "real" | "synthetic";

  type LayerState = Record<LayerKey, boolean>;

  type SelectedObject = {
    type: LayerKey | "unknown";
    id: string;
    properties: Record<string, unknown>;
    entity: any;
  };

  type SearchRecord = {
    id: string;
    type: LayerKey;
    aliases: string[];
    file: string;
  };

  type AiMessage = {
    role: "user" | "assistant";
    text: string;
  };

  const LAYER_FILES: Record<LayerKey, string> = {
    parcels: "/data/geojson/parcels.geojson",
    buildings: "/data/geojson/buildings.geojson",
    floors: "/data/geojson/floors.geojson",
    propertyUnits: "/data/geojson/property_units.geojson",
    underground: "/data/geojson/underground_assets.geojson",
  };

  const REAL_BUILDINGS_FILE = "/data/real/guwahati_buildings_3d.geojson";

  const LAYER_LABELS: Record<LayerKey, string> = {
    parcels: "Parcels",
    buildings: "Buildings",
    floors: "Floors",
    propertyUnits: "Property Units",
    underground: "Underground Assets",
  };

  const SYNTHETIC_STATS = {
    studyAreas: 1,
    parcels: 3,
    buildings: 3,
    floors: 16,
    propertyUnits: 45,
    undergroundAssets: 2,
    indexedEntities: 69,
  };

  const REAL_STATS = {
    studyAreas: 1,
    parcels: 0,
    buildings: 190,
    floors: 983,
    propertyUnits: 2949,
    undergroundAssets: 0,
    indexedEntities: 190,
  };

  const REAL_FLOOR_HEIGHT = 3;

  function App() {
    const viewerRef = useRef<CesiumViewer | null>(null);
    const viewerInitializedRef = useRef(false);
    const clickHandlerRef = useRef<ScreenSpaceEventHandler | null>(null);
    const initialCameraSetRef = useRef(false);

    // One source per synthetic layer. Never mix Resium-managed GeoJSON sources
    // with manually-added sources. That was the main cause of duplicate entities.
    const syntheticSourcesRef = useRef<
      Partial<Record<LayerKey, CesiumGeoJsonDataSource>>
    >({});

    const realBuildingsRef = useRef<CesiumGeoJsonDataSource | null>(null);
    const realBuildingsPromiseRef = useRef<Promise<CesiumGeoJsonDataSource | null> | null>(null);
    const realFloorsRef = useRef<CustomDataSource | null>(null);
    const realPropertyUnitsRef = useRef<CustomDataSource | null>(null);

    const realFloorsBuiltForRef = useRef<Set<string>>(new Set());
    const realUnitsBuiltForRef = useRef<Set<string>>(new Set());

    const searchIndexRef = useRef<SearchRecord[]>([]);
    const searchIndexPromiseRef = useRef<Promise<SearchRecord[]> | null>(null);
    const highlightedEntityRef = useRef<any>(null);

    const [dataMode, setDataMode] = useState<DataMode>("real");
    const dataModeRef = useRef<DataMode>("real");

    const [layers, setLayers] = useState<LayerState>({
      parcels: false,
      buildings: true,
      floors: false,
      propertyUnits: false,
      underground: false,
    });
    const layersRef = useRef<LayerState>({
      parcels: false,
      buildings: true,
      floors: false,
      propertyUnits: false,
      underground: false,
    });

    const [selectedLayer, setSelectedLayer] = useState("None");
    const [selectedObject, setSelectedObject] =
      useState<SelectedObject | null>(null);

    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<SearchRecord[]>([]);
    const [searchMessage, setSearchMessage] = useState("");

    const [aiOpen, setAiOpen] = useState(false);
    const [aiQuestion, setAiQuestion] = useState("");
    const [aiListening, setAiListening] = useState(false);
    const [aiThinking, setAiThinking] = useState(false);
    const [aiMessages, setAiMessages] = useState<AiMessage[]>([
      { role: "assistant", text: "Hello, I am BhuvaAyam AI. Ask me about buildings, floors, height and building IDs." },
    ]);

    const stats = dataMode === "real" ? REAL_STATS : SYNTHETIC_STATS;

    useEffect(() => {
      dataModeRef.current = dataMode;
    }, [dataMode]);

    useEffect(() => {
      layersRef.current = layers;
    }, [layers]);

    useEffect(() => {
      Ion.defaultAccessToken = "";
    }, []);

    const getEntityProperty = (entity: any, key: string): unknown => {
      if (!entity?.properties) return undefined;

      const property = entity.properties[key];
      if (!defined(property)) return undefined;

      try {
        if (typeof property.getValue === "function") {
          return property.getValue(new Date());
        }
      } catch {
        return undefined;
      }

      return property;
    };

    const getEntityProperties = (entity: any): Record<string, unknown> => {
      const result: Record<string, unknown> = {};
      const names = entity?.properties?.propertyNames;

      if (!Array.isArray(names)) return result;

      for (const name of names) {
        result[name] = getEntityProperty(entity, name);
      }

      return result;
    };

    const detectEntityType = (entity: any): LayerKey | "unknown" => {
      if (getEntityProperty(entity, "asset_id")) return "underground";
      if (getEntityProperty(entity, "unit_id")) return "propertyUnits";
      if (getEntityProperty(entity, "floor_id")) return "floors";
      if (getEntityProperty(entity, "building_id")) return "buildings";
      if (getEntityProperty(entity, "parcel_id")) return "parcels";

      const id = entity?.id ? String(entity.id) : "";
      if (/^GHY-B\d+/i.test(id)) return "buildings";

      return "unknown";
    };

    const getEntityId = (entity: any): string => {
      const keys = [
        "asset_id",
        "unit_id",
        "floor_id",
        "building_id",
        "parcel_id",
        "id",
      ];

      for (const key of keys) {
        const value = getEntityProperty(entity, key);
        if (
          value !== undefined &&
          value !== null &&
          String(value).trim() !== ""
        ) {
          return String(value);
        }
      }

      return entity?.id ? String(entity.id) : "UNKNOWN";
    };

    const applyDefaultStyle = (entity: any) => {
      if (!entity?.polygon) return;

      const type = detectEntityType(entity);

      if (type === "parcels") {
        entity.polygon.material = new ColorMaterialProperty(
          Color.YELLOW.withAlpha(0.18)
        );
        entity.polygon.outline = new ConstantProperty(true);
        entity.polygon.outlineColor = new ConstantProperty(Color.YELLOW);
        return;
      }

      if (type === "buildings") {
        entity.polygon.material = new ColorMaterialProperty(
          Color.BLUE.withAlpha(0.55)
        );
        entity.polygon.outline = new ConstantProperty(true);
        entity.polygon.outlineColor = new ConstantProperty(Color.WHITE);
        return;
      }

      if (type === "floors") {
        entity.polygon.material = new ColorMaterialProperty(
          Color.CYAN.withAlpha(0.32)
        );
        entity.polygon.outline = new ConstantProperty(true);
        entity.polygon.outlineColor = new ConstantProperty(Color.CYAN);
        return;
      }

      if (type === "propertyUnits") {
        entity.polygon.material = new ColorMaterialProperty(
          Color.ORANGE.withAlpha(0.28)
        );
        entity.polygon.outline = new ConstantProperty(true);
        entity.polygon.outlineColor = new ConstantProperty(Color.ORANGE);
        return;
      }

      if (type === "underground") {
        entity.polygon.material = new ColorMaterialProperty(
          Color.RED.withAlpha(0.35)
        );
        entity.polygon.outline = new ConstantProperty(true);
        entity.polygon.outlineColor = new ConstantProperty(Color.RED);
      }
    };

    const clearHighlight = () => {
      const previous = highlightedEntityRef.current;
      if (previous) applyDefaultStyle(previous);
      highlightedEntityRef.current = null;
    };

    const highlightEntity = (entity: any) => {
      if (highlightedEntityRef.current === entity) return;

      clearHighlight();

      if (!entity?.polygon) return;

      entity.polygon.material = new ColorMaterialProperty(
        Color.LIME.withAlpha(0.82)
      );
      entity.polygon.outline = new ConstantProperty(true);
      entity.polygon.outlineColor = new ConstantProperty(Color.WHITE);

      highlightedEntityRef.current = entity;
    };

    const styleSource = (
      dataSource: CesiumGeoJsonDataSource,
      layer: LayerKey
    ) => {
      for (const entity of dataSource.entities.values) {
        if (!entity.polygon) continue;

        // Give synthetic building data the same robust 3D treatment as real mode.
        if (layer === "buildings") {
          const height = Number(
            getEntityProperty(entity, "height_m") ??
              getEntityProperty(entity, "height") ??
              getEntityProperty(entity, "building_height")
          );

          if (Number.isFinite(height) && height > 0) {
            entity.polygon.height = new ConstantProperty(0);
            entity.polygon.extrudedHeight = new ConstantProperty(height);
          }
        }

        applyDefaultStyle(entity);
      }
    };

    const ensureSyntheticLayer = async (
      layer: LayerKey
    ): Promise<CesiumGeoJsonDataSource | null> => {
      const viewer = viewerRef.current;
      if (!viewer) return null;

      const cached = syntheticSourcesRef.current[layer];
      if (cached) {
        cached.show = true;
        return cached;
      }

      try {
        const dataSource = await CesiumGeoJsonDataSource.load(
          LAYER_FILES[layer],
          { clampToGround: layer === "parcels" }
        );

        dataSource.name = `SYNTHETIC_${layer.toUpperCase()}`;
        styleSource(dataSource, layer);

        await viewer.dataSources.add(dataSource);
        syntheticSourcesRef.current[layer] = dataSource;

        return dataSource;
      } catch (error) {
        console.error(`Failed to load synthetic ${layer}:`, error);
        return null;
      }
    };

    const ensureRealDerivedSources = async () => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      if (!realFloorsRef.current) {
        const source = new CustomDataSource("REAL_GUWAHATI_DERIVED_FLOORS");
        source.show = false;
        await viewer.dataSources.add(source);
        realFloorsRef.current = source;
      }

      if (!realPropertyUnitsRef.current) {
        const source = new CustomDataSource(
          "REAL_GUWAHATI_DERIVED_PROPERTY_UNITS"
        );
        source.show = false;
        await viewer.dataSources.add(source);
        realPropertyUnitsRef.current = source;
      }
    };

    const getRealBuildingFloorInfo = (building: any) => {
      const heightValue = Number(
        getEntityProperty(building, "height_m") ??
          getEntityProperty(building, "height")
      );

      const floorValue = Number(
        getEntityProperty(building, "floors_estimated") ??
          getEntityProperty(building, "floor_count") ??
          getEntityProperty(building, "levels")
      );

      const floorCount =
        Number.isFinite(floorValue) && floorValue > 0
          ? Math.min(50, Math.max(1, Math.round(floorValue)))
          : Math.min(
              50,
              Math.max(
                1,
                Math.round(
                  (Number.isFinite(heightValue) && heightValue > 0
                    ? heightValue
                    : REAL_FLOOR_HEIGHT) / REAL_FLOOR_HEIGHT
                )
              )
            );

      const totalHeight =
        Number.isFinite(heightValue) && heightValue > 0
          ? heightValue
          : floorCount * REAL_FLOOR_HEIGHT;

      return {
        floorCount,
        totalHeight,
        floorHeight: totalHeight / floorCount,
      };
    };

    const ensureRealBuildingFloors = async (building: any) => {
      if (!building?.polygon) return;

      await ensureRealDerivedSources();

      const source = realFloorsRef.current;
      if (!source) return;

      const buildingId = getEntityId(building);

      if (realFloorsBuiltForRef.current.has(buildingId)) return;

      const { floorCount, floorHeight } = getRealBuildingFloorInfo(building);

      for (let floorIndex = 0; floorIndex < floorCount; floorIndex++) {
        const floorNumber = floorIndex + 1;
        const zMin = floorIndex * floorHeight;
        const zMax = (floorIndex + 1) * floorHeight;
        const floorId = `${buildingId}_F${String(floorNumber).padStart(2, "0")}`;

        source.entities.add({
          id: floorId,
          name: floorId,
          polygon: {
            hierarchy: building.polygon.hierarchy,
            height: new ConstantProperty(zMin),
            extrudedHeight: new ConstantProperty(zMax),
            material: new ColorMaterialProperty(Color.CYAN.withAlpha(0.32)),
            outline: new ConstantProperty(true),
            outlineColor: new ConstantProperty(Color.CYAN),
          },
          properties: new PropertyBag({
            floor_id: floorId,
            building_id: buildingId,
            floor_number: floorNumber,
            floor_height_m: floorHeight,
            z_min: zMin,
            z_max: zMax,
            source: "derived_from_real_building",
          }),
        });
      }

      realFloorsBuiltForRef.current.add(buildingId);
    };

    const ensureRealBuildingUnits = async (building: any) => {
      if (!building?.polygon) return;

      await ensureRealBuildingFloors(building);
      await ensureRealDerivedSources();

      const source = realPropertyUnitsRef.current;
      if (!source) return;

      const buildingId = getEntityId(building);
      if (realUnitsBuiltForRef.current.has(buildingId)) return;

      const { floorCount, floorHeight } = getRealBuildingFloorInfo(building);

      // Prototype units remain explicitly derived, not authoritative records.
      for (let floorIndex = 0; floorIndex < floorCount; floorIndex++) {
        const floorNumber = floorIndex + 1;
        const zMin = floorIndex * floorHeight;
        const zMax = (floorIndex + 1) * floorHeight;
        const floorId = `${buildingId}_F${String(floorNumber).padStart(2, "0")}`;

        for (let unitNumber = 1; unitNumber <= 3; unitNumber++) {
          const unitId = `${floorId}_U${String(unitNumber).padStart(2, "0")}`;

          source.entities.add({
            id: unitId,
            name: unitId,
            polygon: {
              hierarchy: building.polygon.hierarchy,
              height: new ConstantProperty(zMin + 0.08),
              extrudedHeight: new ConstantProperty(
                Math.max(zMin + 0.12, zMax - 0.08)
              ),
              material: new ColorMaterialProperty(
                Color.ORANGE.withAlpha(0.20)
              ),
              outline: new ConstantProperty(true),
              outlineColor: new ConstantProperty(Color.ORANGE),
            },
            properties: new PropertyBag({
              unit_id: unitId,
              building_id: buildingId,
              floor_id: floorId,
              floor_number: floorNumber,
              unit_number: unitNumber,
              unit_type: "prototype_property_unit",
              source: "derived_from_real_building",
              z_min: zMin,
              z_max: zMax,
            }),
          });
        }
      }

      realUnitsBuiltForRef.current.add(buildingId);
    };

    const loadRealGuwahatiBuildings = async () => {
      const viewer = viewerRef.current;
      if (!viewer) return null;

      if (realBuildingsRef.current) {
        realBuildingsRef.current.show = true;
        return realBuildingsRef.current;
      }

      if (realBuildingsPromiseRef.current) {
        return realBuildingsPromiseRef.current;
      }

      realBuildingsPromiseRef.current = (async () => {
        try {
          const dataSource = await CesiumGeoJsonDataSource.load(
            REAL_BUILDINGS_FILE,
            { clampToGround: false }
          );

          dataSource.name = "REAL_GUWAHATI_BUILDINGS";

          for (const entity of dataSource.entities.values) {
            if (!entity.polygon) continue;

            const height = Number(
              getEntityProperty(entity, "height_m") ??
                getEntityProperty(entity, "height")
            );

            entity.polygon.height = new ConstantProperty(0);

            if (Number.isFinite(height) && height > 0) {
              entity.polygon.extrudedHeight = new ConstantProperty(height);
            }

            applyDefaultStyle(entity);
          }

          await viewer.dataSources.add(dataSource);
          realBuildingsRef.current = dataSource;

          return dataSource;
        } catch (error) {
          console.error("Failed to load real Guwahati buildings:", error);
          setSearchMessage(
            "Could not load real Guwahati buildings. Check the browser console."
          );
          return null;
        }
      })();

      const result = await realBuildingsPromiseRef.current;
      realBuildingsPromiseRef.current = null;
      return result;
    };

    const findEntityInSource = (
      source: any,
      type: LayerKey,
      id: string
    ) => {
      if (!source) return null;

      return (
        source.entities.values.find(
          (entity: any) =>
            detectEntityType(entity) === type &&
            getEntityId(entity).toLowerCase() === id.toLowerCase()
        ) ?? null
      );
    };

    const findEntityInViewer = (type: LayerKey, id: string) => {
      const viewer = viewerRef.current;
      if (!viewer) return null;

      for (let i = 0; i < viewer.dataSources.length; i++) {
        const source = viewer.dataSources.get(i);
        const entity = findEntityInSource(source, type, id);
        if (entity) return entity;
      }

      return null;
    };

    const findParentRealBuilding = (buildingId: string) =>
      realBuildingsRef.current?.entities.values.find(
        (entity) =>
          getEntityId(entity).toLowerCase() === buildingId.toLowerCase()
      ) ?? null;

    const selectEntity = async (entity: any) => {
      if (!entity) return;

      const type = detectEntityType(entity);
      const id = getEntityId(entity);
      const properties = getEntityProperties(entity);

      // Update the panel first. Expensive lazy generation happens afterwards.
      setSelectedObject({
        type,
        id,
        properties,
        entity,
      });

      setSelectedLayer(
        type === "unknown" ? "Unknown" : LAYER_LABELS[type]
      );

      highlightEntity(entity);

      if (dataModeRef.current === "real" && type === "buildings") {
        // Floors are generated only for the inspected building.
        await ensureRealBuildingFloors(entity);

        // Units are generated only when that layer is actually requested.
        if (layersRef.current.propertyUnits) {
          await ensureRealBuildingUnits(entity);
        }

        if (layersRef.current.floors && realFloorsRef.current) {
          realFloorsRef.current.show = true;
        }

        if (
          layersRef.current.propertyUnits &&
          realPropertyUnitsRef.current
        ) {
          realPropertyUnitsRef.current.show = true;
        }
      }
    };

    const zoomToEntity = async (entity: any) => {
      const viewer = viewerRef.current;
      if (!viewer || !entity) return;

      try {
        // zoomTo/flyTo is stable for both GeoJSON entities and derived entities.
        // The offset prevents the camera from ending up inside small synthetic data.
        const success = await viewer.flyTo(entity, {
          duration: 1.2,
          offset: new HeadingPitchRange(0, -0.55, 0),
        });

        if (!success) {
          viewer.zoomTo(entity, new HeadingPitchRange(0, -0.55, 0));
        }
      } catch (error) {
        console.error("Failed to zoom to entity:", error);
      }
    };

    const focusSelectedObject = async () => {
      if (!selectedObject) return;

      let entity = findEntityInViewer(
        selectedObject.type === "unknown"
          ? "buildings"
          : selectedObject.type,
        selectedObject.id
      );

      // If React/Cesium recreated an entity, resolve by ID instead of trusting
      // a stale object reference.
      if (!entity) entity = selectedObject.entity;

      await zoomToEntity(entity);
    };

    const zoomToStudyArea = async () => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      try {
        const parcels = await ensureSyntheticLayer("parcels");
        if (!parcels || parcels.entities.values.length === 0) return;

        await viewer.flyTo(parcels.entities.values, {
          duration: 1.5,
          offset: new HeadingPitchRange(0, -0.55, 0),
        });
      } catch (error) {
        console.error("Failed to zoom to synthetic study area:", error);
      }
    };

    const buildSearchIndex = async (): Promise<SearchRecord[]> => {
      if (searchIndexRef.current.length > 0) {
        return searchIndexRef.current;
      }

      if (searchIndexPromiseRef.current) {
        return searchIndexPromiseRef.current;
      }

      searchIndexPromiseRef.current = (async () => {
        const records: SearchRecord[] = [];

        const files: Array<{ type: LayerKey; file: string }> = [
          { type: "parcels", file: LAYER_FILES.parcels },
          { type: "buildings", file: LAYER_FILES.buildings },
          { type: "floors", file: LAYER_FILES.floors },
          { type: "propertyUnits", file: LAYER_FILES.propertyUnits },
          { type: "underground", file: LAYER_FILES.underground },
          { type: "buildings", file: REAL_BUILDINGS_FILE },
        ];

        for (const fileInfo of files) {
          try {
            const response = await fetch(fileInfo.file);
            if (!response.ok) continue;

            const geojson = await response.json();
            const features = Array.isArray(geojson.features)
              ? geojson.features
              : [];

            for (const feature of features) {
              const properties = feature.properties ?? {};

              const rawId =
                properties.asset_id ??
                properties.unit_id ??
                properties.floor_id ??
                properties.building_id ??
                properties.parcel_id ??
                properties.id;

              if (rawId === undefined || rawId === null) continue;

              const id = String(rawId);
              const aliases = new Set<string>([id]);

              for (const value of Object.values(properties)) {
                if (value !== undefined && value !== null) {
                  aliases.add(String(value));
                }
              }

              records.push({
                id,
                type: fileInfo.type,
                aliases: Array.from(aliases),
                file: fileInfo.file,
              });
            }
          } catch (error) {
            console.warn("Search index file failed:", fileInfo.file, error);
          }
        }

        // Remove duplicates while preserving the first record.
        const unique = new Map<string, SearchRecord>();
        for (const record of records) {
          const key = `${record.file}|${record.type}|${record.id}`;
          if (!unique.has(key)) unique.set(key, record);
        }

        searchIndexRef.current = Array.from(unique.values());
        return searchIndexRef.current;
      })();

      return searchIndexPromiseRef.current;
    };

    const findObject = async (record: SearchRecord) => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      setSearchMessage("");

      try {
        if (dataModeRef.current === "real") {
          // In real mode, search results should resolve against the real dataset.
          if (record.file !== REAL_BUILDINGS_FILE) {
            setSearchMessage(
              "Switch to SYNTHETIC mode to inspect prototype cadastral objects."
            );
            return;
          }

          const source = await loadRealGuwahatiBuildings();
          if (!source) return;

          const entity = findEntityInSource(
            source,
            "buildings",
            record.id
          );

          if (!entity) {
            setSearchMessage(`Could not locate ${record.id}`);
            return;
          }

          await selectEntity(entity);
          await zoomToEntity(entity);
          return;
        }

        // Synthetic mode: load only the required cached layer once.
        const source = await ensureSyntheticLayer(record.type);
        if (!source) {
          setSearchMessage(`Could not load ${record.type}`);
          return;
        }

        source.show = true;
        setLayers((current) => ({
          ...current,
          [record.type]: true,
        }));

        const entity = findEntityInSource(
          source,
          record.type,
          record.id
        );

        if (!entity) {
          setSearchMessage(`Could not locate ${record.id}`);
          return;
        }

        await selectEntity(entity);
        await zoomToEntity(entity);
      } catch (error) {
        console.error("Search failed:", error);
        setSearchMessage(`Failed to locate ${record.id}`);
      }
    };

    const handleSearchChange = async (value: string) => {
      setSearchQuery(value);

      if (!value.trim()) {
        setSearchResults([]);
        setSearchMessage("");
        return;
      }

      const index = await buildSearchIndex();
      const query = value.trim().toLowerCase();

      const modeFiltered = index.filter((record) =>
        dataModeRef.current === "real"
          ? record.file === REAL_BUILDINGS_FILE
          : record.file !== REAL_BUILDINGS_FILE
      );

      const results = modeFiltered
        .filter((record) => {
          const haystack = [
            record.id,
            record.type,
            ...record.aliases,
          ]
            .join(" ")
            .toLowerCase();

          return haystack.includes(query);
        })
        .slice(0, 12);

      setSearchResults(results);
      setSearchMessage(
        results.length === 0 ? "No matching cadastral object found." : ""
      );
    };

    const handleSearchKeyDown = async (
      event: KeyboardEvent<HTMLInputElement>
    ) => {
      if (event.key === "Enter" && searchResults.length > 0) {
        await findObject(searchResults[0]);
      }
    };

    const toggleLayer = async (layer: LayerKey) => {
      const next = !layersRef.current[layer];

      if (dataModeRef.current === "real") {
        if (layer === "parcels" || layer === "underground") return;

        if (layer === "buildings") {
          const source = await loadRealGuwahatiBuildings();
          if (!source) return;
          source.show = next;
        }

        if (layer === "floors") {
          if (next && selectedObject?.type === "buildings") {
            await ensureRealBuildingFloors(selectedObject.entity);
          }
          if (realFloorsRef.current) realFloorsRef.current.show = next;
        }

        if (layer === "propertyUnits") {
          if (next && selectedObject?.type === "buildings") {
            await ensureRealBuildingUnits(selectedObject.entity);
          }
          if (realPropertyUnitsRef.current) {
            realPropertyUnitsRef.current.show = next;
          }
        }

        setLayers((current) => ({
          ...current,
          [layer]: next,
        }));
        return;
      }

      if (next) {
        const source = await ensureSyntheticLayer(layer);
        if (!source) return;
        source.show = true;
      } else {
        const source = syntheticSourcesRef.current[layer];
        if (source) source.show = false;
      }

      setLayers((current) => ({
        ...current,
        [layer]: next,
      }));
    };

    const applyDataMode = async (mode: DataMode) => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      clearHighlight();
      setSelectedObject(null);
      setSelectedLayer("None");
      setSearchMessage("");
      setSearchResults([]);

      if (mode === "real") {
        // Hide all synthetic cached sources without unloading them.
        for (const source of Object.values(syntheticSourcesRef.current)) {
          if (source) source.show = false;
        }

        const source = await loadRealGuwahatiBuildings();
        if (!source) return;

        source.show = true;
        if (realFloorsRef.current) realFloorsRef.current.show = false;
        if (realPropertyUnitsRef.current) {
          realPropertyUnitsRef.current.show = false;
        }

        setLayers({
          parcels: false,
          buildings: true,
          floors: false,
          propertyUnits: false,
          underground: false,
        });

        return;
      }

      // Synthetic mode: hide real sources but keep them cached.
      if (realBuildingsRef.current) realBuildingsRef.current.show = false;
      if (realFloorsRef.current) realFloorsRef.current.show = false;
      if (realPropertyUnitsRef.current) {
        realPropertyUnitsRef.current.show = false;
      }

      const parcels = await ensureSyntheticLayer("parcels");
      if (parcels) parcels.show = true;

      for (const [layer, source] of Object.entries(
        syntheticSourcesRef.current
      ) as Array<[LayerKey, CesiumGeoJsonDataSource | undefined]>) {
        if (source && layer !== "parcels") source.show = false;
      }

      setLayers({
        parcels: true,
        buildings: false,
        floors: false,
        propertyUnits: false,
        underground: false,
      });

      // Zoom exactly once after the parcel source is loaded.
      await zoomToStudyArea();
    };

    useEffect(() => {
      if (!viewerInitializedRef.current) return;
      void applyDataMode(dataMode);
    }, [dataMode]);

    const handleViewerReady = (element: any) => {
      const viewer = element?.cesiumElement as CesiumViewer | undefined;
      if (!viewer) return;

      viewerRef.current = viewer;

      if (viewerInitializedRef.current) return;
      viewerInitializedRef.current = true;

      viewer.scene.screenSpaceCameraController.enableZoom = true;
      viewer.scene.screenSpaceCameraController.enableRotate = true;
      viewer.scene.screenSpaceCameraController.enableTranslate = true;
      viewer.scene.screenSpaceCameraController.enableTilt = true;
      viewer.scene.screenSpaceCameraController.enableLook = true;
      viewer.scene.screenSpaceCameraController.enableCollisionDetection = false;

      if (!initialCameraSetRef.current) {
        initialCameraSetRef.current = true;
        viewer.camera.flyTo({
          destination: Cartesian3.fromDegrees(91.7362, 26.1445, 10000),
          duration: 0.8,
        });
      }

      if (clickHandlerRef.current) clickHandlerRef.current.destroy();

      const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);

      handler.setInputAction(
        (movement: any) => {
          try {
            const picked = viewer.scene.pick(movement.position);

            // IMPORTANT: background clicks do nothing. They do not clear the panel.
            if (!defined(picked) || !defined(picked.id)) return;

            const entity = picked.id?.entity ?? picked.id;
            if (!entity) return;

            void selectEntity(entity);
          } catch (error) {
            console.error("Entity click failed:", error);
          }
        },
        ScreenSpaceEventType.LEFT_CLICK
      );

      clickHandlerRef.current = handler;

      // No delayed setTimeout that can re-apply an old mode and wipe selection.
      void applyDataMode(dataModeRef.current);
      void buildSearchIndex();
    };

    useEffect(() => {
      return () => {
        if (clickHandlerRef.current) {
          clickHandlerRef.current.destroy();
          clickHandlerRef.current = null;
        }
      };
    }, []);

    const formatValue = (value: unknown): string => {
      if (value === null || value === undefined) return "—";

      if (typeof value === "number") {
        return Number.isInteger(value) ? String(value) : value.toFixed(3);
      }

      if (typeof value === "object") {
        try {
          return JSON.stringify(value);
        } catch {
          return String(value);
        }
      }

      return String(value);
    };

    const normalizeAiText = (value: unknown) =>
      String(value ?? "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim();

    const speakAiAnswer = (text: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-IN";
      utterance.rate = 1;
      window.speechSynthesis.speak(utterance);
    };

    const findAiBuildingRecord = async (question: string) => {
      const index = await buildSearchIndex();
      const q = normalizeAiText(question);
      const records = index.filter((record) =>
        dataModeRef.current === "real"
          ? record.file === REAL_BUILDINGS_FILE
          : record.type === "buildings"
      );

      let best: SearchRecord | null = null;
      let bestScore = 0;

      for (const record of records) {
        for (const alias of [record.id, ...record.aliases]) {
          const candidate = normalizeAiText(alias);
          if (candidate.length < 3 || /^\d+(?: \d+)*$/.test(candidate)) continue;
          const tokens = candidate.split(" ").filter((token) => token.length >= 3);
          const matches = tokens.filter((token) => q.includes(token)).length;
          if (!matches) continue;
          const score = matches * 100 + candidate.length + (q.includes(candidate) ? 1000 : 0);
          if (score > bestScore) {
            bestScore = score;
            best = record;
          }
        }
      }

      return bestScore >= 100 ? best : null;
    };

    const answerSpatialQuestion = async (question: string) => {
      const q = normalizeAiText(question);
      const wantsFloors = /how many floors|number of floors|floor count|floors|levels|storeys|stories/.test(q);
      const wantsHeight = /height|how tall|tall/.test(q);
      const wantsId = /building id|what is the id|ul?pin/.test(q);

      const refersToSelectedBuilding = /selected building|this building|current building/.test(q);
      const selectedBuilding =
        refersToSelectedBuilding && selectedObject?.type === "buildings"
          ? selectedObject.entity
          : null;

      const record = selectedBuilding
        ? null
        : await findAiBuildingRecord(question);

      if (!selectedBuilding && !record) {
        return "I could not confidently match that building in the current map dataset. Try the exact building name, block name, or building ID.";
      }

      const entity = selectedBuilding
        ? selectedBuilding
        : findEntityInSource(
            record!.file === REAL_BUILDINGS_FILE
              ? await loadRealGuwahatiBuildings()
              : await ensureSyntheticLayer("buildings"),
            "buildings",
            record!.id
          );

      if (!entity) {
        return "I found a matching building record, but I could not load its geometry and metadata.";
      }

      await selectEntity(entity);
      await zoomToEntity(entity);

      const properties = getEntityProperties(entity);
      const resolvedId = record?.id ?? getEntityId(entity);
      const buildingName = String(
        properties.name ?? properties.building_name ?? properties.title ?? resolvedId
      ) || resolvedId;
      const floorInfo = getRealBuildingFloorInfo(entity);

      if (wantsFloors) {
        return `${buildingName} has ${floorInfo.floorCount} floor${floorInfo.floorCount === 1 ? "" : "s"} according to the building levels or height available in the current dataset.`;
      }

      if (wantsHeight) {
        const height = Number(properties.height_m ?? properties.height ?? properties.building_height);
        if (Number.isFinite(height) && height > 0) {
          return `${buildingName} is approximately ${height.toFixed(1)} metres tall according to the dataset.`;
        }
        return `${buildingName} has an estimated height of ${floorInfo.totalHeight.toFixed(1)} metres based on its available floor information.`;
      }

      if (wantsId) {
        return `The building ID for ${buildingName} is ${resolvedId}.`;
      }

      return `${buildingName} is selected on the map. It has an estimated ${floorInfo.floorCount} floor${floorInfo.floorCount === 1 ? "" : "s"}. Ask me about its floors, height or building ID.`;
    };

    const submitAiQuestion = async (question: string) => {
      const cleanQuestion = question.trim();
      if (!cleanQuestion || aiThinking) return;

      setAiQuestion("");
      setAiMessages((current) => [...current, { role: "user", text: cleanQuestion }]);
      setAiThinking(true);

      try {
        const answer = await answerSpatialQuestion(cleanQuestion);
        setAiMessages((current) => [...current, { role: "assistant", text: answer }]);
        speakAiAnswer(answer);
      } catch (error) {
        console.error("Bhuyaam AI query failed:", error);
        const answer = "I could not complete that spatial query. Please try again with a building name or building ID.";
        setAiMessages((current) => [...current, { role: "assistant", text: answer }]);
        speakAiAnswer(answer);
      } finally {
        setAiThinking(false);
      }
    };

    const startAiVoiceInput = () => {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setAiMessages((current) => [
          ...current,
          { role: "assistant", text: "Voice input is not supported in this browser. Please use Chrome or Edge, or type your question." },
        ]);
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = "en-IN";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onstart = () => setAiListening(true);
      recognition.onerror = () => setAiListening(false);
      recognition.onend = () => setAiListening(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript ?? "";
        setAiQuestion(transcript);
        if (transcript.trim()) void submitAiQuestion(transcript);
      };
      recognition.start();
    };

    const renderPropertyRows = (
      properties: Record<string, unknown>
    ) => {
      const entries = Object.entries(properties);

      if (entries.length === 0) {
        return <div className="empty-state">No metadata available.</div>;
      }

      return entries.map(([key, value]) => (
        <div className="property-row" key={key}>
          <div className="property-key">{key}</div>
          <div className="property-value">{formatValue(value)}</div>
        </div>
      ));
    };
return (
  <div className="app-shell">

    {/* =====================================================
        TOP NAVIGATION
    ===================================================== */}
    <header className="topbar">

      {/* BRAND */}
      <div className="brand-area">
        <div className="brand-logo">
          <div className="logo-mark"></div>

          <div>
            <div className="brand-name">BhuvaAyam</div>

            <div className="brand-tagline">
              3D ULPIN · LAND INTELLIGENCE PLATFORM
            </div>
          </div>
        </div>
      </div>


      {/* TOP NAVIGATION BUTTONS */}
      <nav className="top-navigation">

        <button
          type="button"
          className="nav-item active"
        >
          <span className="nav-icon">⌂</span>
          <span>Dashboard</span>
        </button>

        

        <button
          type="button"
          className="nav-item"
        >
          <span className="nav-icon">⌘</span>
          <span>Developers</span>
        </button>

        <button
          type="button"
          className="nav-item"
        >
          <span className="nav-icon">●</span>
          <span>About</span>
        </button>

        <button
          type="button"
          className="nav-item"
        >
          <span className="nav-icon">?</span>
          <span>Help</span>
        </button>

      </nav>


      {/* STATUS */}
      <div className="top-status">

        <div className="online-status">
          <span className="status-dot" />
          <span>GIS ONLINE</span>
        </div>

        <div className="language-button">
          <span>IN</span>
        </div>

      </div>

    </header>


    {/* =====================================================
        MAIN DASHBOARD
    ===================================================== */}
    <div className="dashboard-layout">


      {/* =====================================================
          LEFT SIDEBAR
      ===================================================== */}
      <aside className="left-sidebar">

        {/* DATA ECOSYSTEM */}
        <section className="panel-section">

          <div className="panel-title">
            <span className="panel-title-icon">▤</span>
            <span>DATA ECOSYSTEM</span>
          </div>


          <button
            type="button"
            className={
              dataMode === "real"
                ? "data-mode-button active"
                : "data-mode-button"
            }
            onClick={() => setDataMode("real")}
          >
            <span className="mode-button-icon">▤</span>

            <span className="mode-button-content">
              <strong>Real Data</strong>
              <small>(Guwahati)</small>
            </span>
          </button>


          <button
            type="button"
            className={
              dataMode === "synthetic"
                ? "data-mode-button active"
                : "data-mode-button"
            }
            onClick={() => setDataMode("synthetic")}
          >
            <span className="mode-button-icon">▤</span>

            <span className="mode-button-content">
              <strong>Model / Synthetic</strong>
            </span>
          </button>

        </section>


        {/* SPATIAL LAYERS */}
        <section className="panel-section spatial-section">

          <div className="panel-header">

            <div className="panel-title">
              <span className="panel-title-icon">◈</span>
              <span>SPATIAL LAYERS</span>
            </div>

            <span className="layer-count">
              {Object.values(layers).filter(Boolean).length} ACTIVE
            </span>

          </div>


          <div className="layer-list">

            {(
              [
                ["parcels", "▱", "Parcels"],
                ["buildings", "▦", "Buildings"],
                ["floors", "≡", "Floors"],
                ["propertyUnits", "⌂", "Property Units"],
                ["underground", "⌁", "Underground Assets"],
              ] as [LayerKey, string, string][]
            ).map(([layer, icon, label]) => {

              const disabled =
                dataMode === "real" &&
                (
                  layer === "parcels" ||
                  layer === "underground"
                );

              return (
                <button
                  key={layer}
                  type="button"
                  disabled={disabled}
                  className={
                    disabled
                      ? "layer-row disabled"
                      : layers[layer]
                        ? "layer-row active"
                        : "layer-row"
                  }
                  onClick={() => void toggleLayer(layer)}
                >

                  <span
                    className={
                      layers[layer]
                        ? "layer-checkbox checked"
                        : "layer-checkbox"
                    }
                  >
                    {layers[layer] ? "✓" : ""}
                  </span>


                  <span className="layer-icon">
                    {icon}
                  </span>


                  <span className="layer-name">
                    {label}
                  </span>

                </button>
              );
            })}

          </div>

        </section>


        {/* SMART ASSISTANT */}
        <section className="assistant-section">

          <div className="panel-title">
            <span className="panel-title-icon">♙</span>
            <span>SMART ASSISTANT</span>
          </div>


          <button
            type="button"
            className="ask-ai-button"
            onClick={() => setAiOpen(true)}
          >
            <span className="ask-ai-icon">✦</span>

            <span>Ask BhuvaAyam AI</span>

            <span className="ask-ai-arrow">›</span>
          </button>

        </section>


        {/* INDIA / DIGITAL GOVERNANCE STYLE CARD */}
        <div className="vikshit-card">

          <div className="india-map-mark">
            <span>India</span>
          </div>

          <div className="vikshit-text">
            <strong>Viksit Bharat</strong>
            <span>Through</span>
            <span>Digital Land Governance</span>
          </div>

        </div>

      </aside>


      {/* =====================================================
          CENTER MAP AREA
      ===================================================== */}
      <section className="center-workspace">


        {/* SEARCH BAR */}
        <div className="map-searchbar">

          <div className="search-field">

            <span className="search-icon">⌕</span>

            <input
              value={searchQuery}
              onChange={(event) =>
                void handleSearchChange(event.target.value)
              }
              onKeyDown={handleSearchKeyDown}
              placeholder={
                dataMode === "real"
                  ? "Search by Building ID, Parcel ID, ULPIN, Address..."
                  : "Search Parcel, Building, Floor or Property Unit..."
              }
            />

            <span className="search-shortcut">
              Ctrl + K
            </span>

          </div>


          {searchResults.length > 0 && (
            <div className="search-dropdown">

              {searchResults.map((result) => (
                <button
                  key={`${result.file}-${result.type}-${result.id}`}
                  type="button"
                  className="search-result-item"
                  onClick={() => void findObject(result)}
                >

                  <div className="result-id">
                    {result.id}
                  </div>

                  <div className="result-type">
                    {LAYER_LABELS[result.type]}
                  </div>

                </button>
              ))}

            </div>
          )}


          {searchMessage && (
            <div className="search-message">
              {searchMessage}
            </div>
          )}

        </div>


        {/* MAP LOCATION */}
        <div className="map-location">

          <span className="location-pin">●</span>

          <span>
            Guwahati, Assam
          </span>

          <span className="location-arrow">
            ˅
          </span>

        </div>


        {/* MAP */}
        <div className="map-frame">

          <Viewer
            full
            animation={false}
            timeline={false}
            baseLayerPicker={false}
            geocoder={false}
            homeButton={false}
            navigationHelpButton={false}
            sceneModePicker={false}
            selectionIndicator={false}
            infoBox={false}
            fullscreenButton={false}
            ref={handleViewerReady}
          />


          {/* COMPASS */}
          <div className="map-compass">
            <span className="compass-n">N</span>
            <span className="compass-arrow">▲</span>
          </div>


          {/* MAP VIEW LABEL */}
          <div className="map-view-label">

            <span className="map-view-indicator" />

            <span>
              3D View
            </span>

            <span className="map-view-divider">
              |
            </span>

            <strong>
              Guwahati, Assam
            </strong>

          </div>


          {/* MAP CONTROLS */}
          <div className="map-controls">

            <button
              type="button"
              title="Zoom In"
              onClick={() => {
                const viewer = viewerRef.current;
                if (!viewer) return;

                viewer.camera.zoomIn(
                  viewer.camera.positionCartographic.height * 0.2
                );
              }}
            >
              +
            </button>


            <button
              type="button"
              title="Zoom Out"
              onClick={() => {
                const viewer = viewerRef.current;
                if (!viewer) return;

                viewer.camera.zoomOut(
                  viewer.camera.positionCartographic.height * 0.2
                );
              }}
            >
              −
            </button>


            <div className="control-divider" />


            <button
              type="button"
              title="Home View"
              onClick={() => {
                const viewer = viewerRef.current;
                if (!viewer) return;

                viewer.camera.flyTo({
                  destination:
                    Cartesian3.fromDegrees(
                      91.7362,
                      26.1445,
                      10000
                    ),
                  duration: 0.8,
                });
              }}
            >
              ⌂
            </button>


            <button
              type="button"
              title="Focus Selected Object"
              onClick={() =>
                void focusSelectedObject()
              }
            >
              ⌖
            </button>


            <button
              type="button"
              title="Layers"
            >
              ▱
            </button>


            <button
              type="button"
              title="Fullscreen"
              onClick={() => {
                const element =
                  document.documentElement;

                if (
                  !document.fullscreenElement
                ) {
                  void element.requestFullscreen?.();
                } else {
                  void document.exitFullscreen?.();
                }
              }}
            >
              ↗
            </button>

          </div>


          {/* COORDINATES */}
          <div className="map-coordinates">

            <span>Lat: 26.1445° N</span>

            <span>Lon: 91.7362° E</span>

            <span>Elev: 128 m</span>

          </div>


          {/* MAP ATTRIBUTION */}
          <div className="map-attribution">
          
          
          </div>

        </div>

      </section>


      {/* =====================================================
          RIGHT PROPERTY INSPECTOR
      ===================================================== */}
      <aside className="right-sidebar">

        <div className="inspector-header">

          <span className="inspector-header-icon">
            ▤
          </span>

          <span>
            PROPERTY INSPECTOR
          </span>

        </div>


        <div className="inspector-card">

          {!selectedObject && (

            <div className="no-selection">

              <div className="property-building-icon">
                ▦
              </div>

              <div className="no-selection-title">
                No Property Selected
              </div>

              <p>
                Click a building or spatial object
                on the map to inspect its details.
              </p>

            </div>

          )}


          {selectedObject && (

            <>
              {/* OBJECT HEADER */}
              <div className="selected-property-header">

                <div className="property-building-icon">
                  ▦
                </div>


                <div className="selected-property-heading">

                  <span>
                    {selectedLayer}
                  </span>

                  <strong>
                    {selectedObject.id}
                  </strong>

                </div>

              </div>


              {/* TABS */}
              <div className="inspector-tabs">

                <button
                  type="button"
                  className="inspector-tab active"
                >
                  Overview
                </button>

                <button
                  type="button"
                  className="inspector-tab"
                >
                  Attributes
                </button>

                <button
                  type="button"
                  className="inspector-tab"
                >
                  Related
                </button>

              </div>


              {/* METADATA */}
              <div className="metadata-list">

                {renderPropertyRows(
                  selectedObject.properties
                )}

              </div>


              {/* ZOOM BUTTON */}
              <button
                type="button"
                className="zoom-building-button"
                onClick={() =>
                  void focusSelectedObject()
                }
              >

                <span>
                  ⌖
                </span>

                <span>
                  Zoom to Building
                </span>

              </button>

            </>

          )}

        </div>

      </aside>

    </div>


    {/* =====================================================
        BOTTOM STATISTICS
    ===================================================== */}
    <footer className="bottom-statistics">


      {/* SYSTEM STATISTICS */}
      <div className="statistics-title">

        <div className="statistics-icon">
          ▮▮▮
        </div>

        <div>
          <strong>
            SYSTEM STATISTICS
          </strong>

          <span>
            Guwahati City Dataset (
            {dataMode === "real"
              ? "Real Data"
              : "Synthetic"}
            )
          </span>
        </div>

      </div>


      {/* BUILDINGS */}
      <div className="bottom-stat-item">

        <span className="bottom-stat-icon">
          ▦
        </span>

        <div>
          <strong>
            {stats.buildings.toLocaleString()}
          </strong>

          <span>
            Buildings
          </span>
        </div>

      </div>


      {/* FLOORS */}
      <div className="bottom-stat-item">

        <span className="bottom-stat-icon">
          ▱
        </span>

        <div>
          <strong>
            {stats.floors.toLocaleString()}
          </strong>

          <span>
            Floors
          </span>
        </div>

      </div>


      {/* PROPERTY UNITS */}
      <div className="bottom-stat-item">

        <span className="bottom-stat-icon">
          ⌂
        </span>

        <div>
          <strong>
            {stats.propertyUnits.toLocaleString()}
          </strong>

          <span>
            Property Units
          </span>
        </div>

      </div>


      {/* UNDERGROUND */}
      <div className="bottom-stat-item">

        <span className="bottom-stat-icon">
          ⌁
        </span>

        <div>
          <strong>
            {stats.undergroundAssets.toLocaleString()}
          </strong>

          <span>
            Underground Assets
          </span>
        </div>

      </div>


      {/* LIVE */}
      <div className="live-system-status">

        <span className="status-dot" />

        <div>

          <strong>
            LIVE
          </strong>

          <span>
            All Systems Operational
          </span>

        </div>

      </div>


      {/* DIGITAL INDIA STYLE */}
      <div className="digital-india-footer">

        <strong>
          Digital India
        </strong>

        <span>
          Land for a Better Tomorrow
        </span>

      </div>

    </footer>

    {aiOpen && (
      <div className="ai-overlay" role="dialog" aria-modal="true" aria-label="BhuvaAyam AI Assistant">
        <div className="ai-modal">
          <div className="ai-modal-header">
            <div>
              <strong>✦ BhuvaAyam AI</strong>
              <span>Spatial Intelligence Assistant</span>
            </div>
            <button type="button" className="ai-close-button" onClick={() => setAiOpen(false)}>×</button>
          </div>

          <div className="ai-messages">
            {aiMessages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={message.role === "assistant" ? "ai-message assistant" : "ai-message user"}
              >
                <span>{message.text}</span>
                {message.role === "assistant" && (
                  <button type="button" className="ai-speak-button" title="Speak answer" onClick={() => speakAiAnswer(message.text)}>🔊</button>
                )}
              </div>
            ))}
            {aiThinking && <div className="ai-message assistant ai-thinking">Bhuyaam AI is analysing the spatial dataset…</div>}
          </div>

          <div className="ai-suggestions">
            <button type="button" onClick={() => void submitAiQuestion("How many floors are there in Assam Down Town University B Block?")}>How many floors are there?</button>
            <button type="button" onClick={() => void submitAiQuestion("What is the height of the selected building?")}>What is the building height?</button>
          </div>

          <form className="ai-input-row" onSubmit={(event) => { event.preventDefault(); void submitAiQuestion(aiQuestion); }}>
            <input
              value={aiQuestion}
              onChange={(event) => setAiQuestion(event.target.value)}
              placeholder="Ask about a building, floors, height or ID…"
              disabled={aiThinking}
            />
            <button
              type="button"
              className={aiListening ? "ai-voice-button listening" : "ai-voice-button"}
              title="Ask by voice"
              onClick={startAiVoiceInput}
              disabled={aiThinking}
            >🎙</button>
            <button type="submit" className="ai-send-button" disabled={!aiQuestion.trim() || aiThinking}>Ask</button>
          </form>

          <div className="ai-disclaimer">Answers are grounded in the buildings and cadastral data currently available in this application.</div>
        </div>
      </div>
    )}

  </div>
);
}

export default App;