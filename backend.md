# Django Clean Architecture Guide

## Overview

This guide documents the clean architecture pattern implemented in the **connections app** and serves as a reference for refactoring other Django apps in this codebase.

**Core Principle**: Separate business logic from database concerns through layered architecture.

```
HTTP Request → View (thin wrapper) → Service Layer (business logic) → Repository (ORM) → Database
```

**Benefits:**

- ✅ **Testable**: Pure unit tests without database (fast!)
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Scalable**: Easy to swap implementations
- ✅ **Readable**: Each layer has a single responsibility

This architecture is derived from:

- **DDD** (Domain-Driven Design)
- **Hexagonal Architecture** / Ports & Adapters
- **Enterprise Django patterns**

---

## Reference Implementation: `apps/connections`

The **connections** app is the canonical example of this architecture. Use it as a blueprint when refactoring other apps.

### Folder Structure

```
apps/connections/
├── api/
│   └── v1/
│       ├── views.py           # ViewSet - thin HTTP wrappers
│       ├── serializers.py     # DRF serializers
│       ├── services.py        # DEPRECATED - backwards compatibility only
│       ├── examples.py        # OpenAPI examples
│       └── urls.py            # URL routing
├── services/
│   ├── dag_service.py         # Business logic (DB-independent)
│   └── power_status_analyzer.py  # Domain logic
├── repositories/
│   ├── connection_repository.py  # ORM queries for connections
│   ├── asset_repository.py       # ORM queries for assets
│   └── facility_repository.py    # ORM queries for facilities
├── tests/
│   ├── test_services.py       # Unit tests (no DB, uses mocks)
│   └── test_api_schema.py     # Integration tests (with DB)
├── models.py                  # Django models
└── admin.py                   # Django admin
```

---

## Layer 1: Views (HTTP Layer) - KEEP IT THIN

**Rule**: Views should ONLY handle HTTP concerns. No business logic!

### What Views Should Do:

- ✅ Extract request parameters
- ✅ Instantiate repositories and services
- ✅ Call service methods
- ✅ Return HTTP responses
- ✅ Handle HTTP errors (400, 404, 500)

### What Views Should NOT Do:

- ❌ Business logic
- ❌ Direct ORM queries
- ❌ Complex calculations
- ❌ Data transformations

### Example: AssetConnectionViewSet

```python
# apps/connections/api/v1/views.py

class AssetConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing asset connections - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.connection_repo = ConnectionRepository()
        self.asset_repo = AssetRepository()
        self.facility_repo = FacilityRepository()
        self.power_analyzer = PowerStatusAnalyzer()

        # Inject service with dependencies
        self.dag_service = DagService(
            self.connection_repo,
            self.asset_repo,
            self.facility_repo,
            self.power_analyzer,
        )

    @action(detail=False, methods=["get"])
    def facility_dag(self, request):
        """Get facility DAG - delegates to service layer."""
        facility_id = request.query_params.get("facility_id")

        if not facility_id:
            return Response(
                {"error": "facility_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get measurements data (external service call)
        measurements_response = get_facility_latest_measurements(facility_id)
        measurements_data = {}
        if measurements_response and "measurements" in measurements_response:
            for measurement in measurements_response["measurements"]:
                measurements_data[measurement["equipment_id"]] = measurement

        # Delegate business logic to service
        response_data, code = self.dag_service.generate_filtered_dag(
            facility_id, downstream_of, upstream_of, measurements_data
        )

        if code != 200:
            return Response(response_data, status=code)

        # Serialize and return
        serializer = FacilityConnectionsSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**Notice:**

- View only handles HTTP request/response
- All business logic delegated to `dag_service`
- Repository dependencies injected in `__init__`
- Clear separation of concerns

---

## Layer 2: Services (Business Logic) - NO ORM!

**Rule**: Services contain business logic and MUST NOT import Django models or use ORM directly.

### What Services Should Do:

- ✅ Implement business logic
- ✅ Orchestrate repository calls
- ✅ Transform and process data
- ✅ Validate business rules
- ✅ Accept dependencies via constructor injection

### What Services Should NOT Do:

- ❌ Import Django models
- ❌ Use `.objects.filter()` or any ORM methods
- ❌ Make database queries directly
- ❌ Handle HTTP concerns

### Example: DagService

```python
# apps/connections/services/dag_service.py

class DagService:
    """Service for generating DAG (Directed Acyclic Graph) representations."""

    def __init__(
        self,
        connection_repo,    # Repository interface
        asset_repo,         # Repository interface
        facility_repo,      # Repository interface
        power_analyzer,     # Domain service
    ):
        """
        Initialize service with repository dependencies.

        Args:
            connection_repo: ConnectionRepository instance
            asset_repo: AssetRepository instance
            facility_repo: FacilityRepository instance
            power_analyzer: PowerStatusAnalyzer instance
        """
        self.connection_repo = connection_repo
        self.asset_repo = asset_repo
        self.facility_repo = facility_repo
        self.power_analyzer = power_analyzer

    def generate_facility_dag(
        self, facility_id: str, measurements_data: dict | None = None
    ) -> tuple[dict[str, Any], int]:
        """
        Generate full facility DAG with all assets and connections.

        Pure business logic - no ORM calls!

        Args:
            facility_id: UUID of the facility
            measurements_data: Optional pre-fetched measurements data

        Returns:
            Tuple of (response_data, status_code)
        """
        # Check facility exists (via repository)
        facility = self.facility_repo.get_by_id(facility_id)
        if not facility:
            return {"error": "Facility not found"}, 404

        # Get data via repositories (no direct ORM!)
        facility_assets = self.asset_repo.get_facility_assets_with_details(facility_id)
        asset_dict = self.asset_repo.create_asset_dict(facility_assets)

        asset_ids = list(asset_dict.keys())
        connections = self.connection_repo.get_facility_connections(asset_ids)

        # Business logic: Build nodes with location caching
        nodes = []
        location_cache: dict[Any, str] = {}

        for asset_id, asset in asset_dict.items():
            if asset.location and asset.location.id not in location_cache:
                location_cache[asset.location.id] = str(asset.location)

            nodes.append({
                "id": asset_id,
                "type": asset.asset_type,
                "data": {
                    "label": asset.name,
                    "asset_type": asset.asset_type,
                    "operational_status": asset.operational_status,
                    "location": (location_cache.get(asset.location.id) if asset.location else None),
                }
            })

        # Business logic: Analyze power statuses
        power_statuses = self.power_analyzer.analyze_facility_connections(
            connections, measurements_data
        )

        # Business logic: Build edges
        edges = []
        for connection in connections:
            edges.append({
                "id": str(connection.id),
                "source": str(connection.source_object_id),
                "target": str(connection.target_object_id),
                "data": {
                    "connection_type": connection.connection_type,
                    "is_powered": power_statuses.get(str(connection.id), False),
                }
            })

        response_data = {
            "nodes": nodes,
            "edges": edges,
            "facility_id": str(facility.id),
            "facility_name": facility.name,
            "total_assets": len(nodes),
            "total_connections": len(edges),
        }
        return response_data, 200

    def _find_downstream_assets(self, asset_id: str, connections_query) -> set[str]:
        """Find all downstream assets from a starting asset - pure logic."""
        downstream_connections = [
            c for c in connections_query
            if str(c.source_object_id) == asset_id
        ]
        downstream_asset_ids = {asset_id}

        while downstream_connections:
            current_asset_ids = [str(c.target_object_id) for c in downstream_connections]
            downstream_asset_ids.update(current_asset_ids)
            downstream_connections = [
                c for c in connections_query
                if str(c.source_object_id) in current_asset_ids
            ]

        return downstream_asset_ids
```

**Notice:**

- No Django imports (`from django.db`, `from apps.*.models`)
- All database access via repository methods
- Pure business logic - easily testable
- Dependencies injected via constructor

### Example: PowerStatusAnalyzer

```python
# apps/connections/services/power_status_analyzer.py

class PowerStatusAnalyzer:
    """
    Domain service for analyzing power flow through connections.

    Pure logic - no database dependencies.
    """

    def analyze_facility_connections(
        self, connections, measurements_data: dict | None = None
    ) -> dict[str, bool]:
        """
        Analyze power status for multiple connections in a single call.

        Args:
            connections: List of connection objects (from repository)
            measurements_data: Optional pre-fetched measurements data

        Returns:
            Dictionary mapping connection IDs to their power status
        """
        # Business logic: cache power calculations
        asset_power_cache = {}
        results = {}

        for connection in connections:
            # Get source power (with caching)
            source_id = str(connection.source_object_id)
            if source_id not in asset_power_cache:
                asset_power_cache[source_id] = self._get_asset_power_by_id(
                    source_id, measurements_data
                )
            source_power = asset_power_cache[source_id]

            # Get target power (with caching)
            target_id = str(connection.target_object_id)
            if target_id not in asset_power_cache:
                asset_power_cache[target_id] = self._get_asset_power_by_id(
                    target_id, measurements_data
                )
            target_power = asset_power_cache[target_id]

            # Business rule: power flows if both ends have power > 0
            is_powered = abs(target_power) > 0 and abs(source_power) > 0
            results[str(connection.id)] = is_powered

        return results
```

---

## Layer 3: Repositories (ORM Layer) - ONLY Database Access

**Rule**: Repositories are the ONLY place where ORM queries should exist.

### What Repositories Should Do:

- ✅ Encapsulate all ORM queries
- ✅ Use `select_related()` and `prefetch_related()` for optimization
- ✅ Return Django model instances or QuerySets
- ✅ Provide simple, focused query methods
- ✅ Handle database-level filtering

### What Repositories Should NOT Do:

- ❌ Business logic
- ❌ Data transformations (beyond simple dictionaries)
- ❌ Complex calculations
- ❌ HTTP handling

### Example: ConnectionRepository

```python
# apps/connections/repositories/connection_repository.py

from django.db.models import QuerySet
from apps.connections.models import AssetConnection

class ConnectionRepository:
    """Repository for managing AssetConnection data access."""

    def get_by_id(self, connection_id: str) -> AssetConnection | None:
        """Get a connection by ID."""
        try:
            return AssetConnection.objects.select_related(
                "source_content_type", "target_content_type"
            ).get(id=connection_id)
        except AssetConnection.DoesNotExist:
            return None

    def get_active_connections(self) -> QuerySet[AssetConnection]:
        """Get all active connections with optimized query."""
        return AssetConnection.objects.filter(is_active=True).select_related(
            "source_content_type", "target_content_type"
        )

    def get_facility_connections(
        self, asset_ids: list[str]
    ) -> QuerySet[AssetConnection]:
        """Get all connections within a facility."""
        return AssetConnection.objects.filter(
            source_object_id__in=asset_ids,
            target_object_id__in=asset_ids,
            is_active=True,
        ).select_related("source_content_type", "target_content_type")

    def get_downstream_connections(self, asset_id: str) -> list[AssetConnection]:
        """Get all downstream connections from a specific asset."""
        return list(
            AssetConnection.objects.filter(
                source_object_id=asset_id, is_active=True
            ).select_related("source_content_type", "target_content_type")
        )

    def filter_by_organization(
        self, queryset: QuerySet[AssetConnection], organization_id: str
    ) -> QuerySet[AssetConnection]:
        """Filter connections by organization using content types."""
        asset_content_types = ContentType.objects.filter(
            model__in=[
                "ups", "generator", "breaker",
                "powerqualitymeter", "grid", "powerprotectionsystem"
            ]
        )
        return queryset.filter(
            Q(source_content_type__in=asset_content_types) |
            Q(target_content_type__in=asset_content_types)
        )
```

### Example: AssetRepository

```python
# apps/connections/repositories/asset_repository.py

from django.db.models import QuerySet
from apps.assets.models import BaseAsset

class AssetRepository:
    """Repository for managing BaseAsset data access in connections context."""

    def get_by_id(self, asset_id: str) -> BaseAsset | None:
        """Get an asset by ID with facility relationship."""
        try:
            return BaseAsset.objects.select_related("facility").get(id=asset_id)
        except BaseAsset.DoesNotExist:
            return None

    def get_facility_assets_with_details(
        self, facility_id: str
    ) -> QuerySet[BaseAsset]:
        """
        Get facility assets with optimized field selection for DAG generation.

        Uses .only() to fetch only required fields for performance.
        """
        return (
            BaseAsset.objects.filter(facility_id=facility_id)
            .only(
                "id", "name", "operational_status", "electrical_system",
                "serial_number", "make", "model", "asset_tag",
                "location", "asset_type"
            )
            .select_related("location")
        )

    def create_asset_dict(
        self, assets: QuerySet[BaseAsset]
    ) -> dict[str, BaseAsset]:
        """Convert queryset to dictionary keyed by string ID."""
        return {str(asset.id): asset for asset in assets}

    def create_location_groups(
        self, assets: QuerySet[BaseAsset]
    ) -> dict[str, dict[str, Any]]:
        """
        Group assets by location - simple data transformation in repository.

        This is acceptable in repository because it's data-structure transformation,
        not business logic.
        """
        from collections import defaultdict

        location_groups = defaultdict(
            lambda: {"location_id": "", "location_name": "", "assets": []}
        )

        for asset in assets:
            location_id = str(asset.location.id) if asset.location else "unknown"
            location_name = asset.location.name if asset.location else "Unknown Location"

            if not location_groups[location_id]["location_id"]:
                location_groups[location_id]["location_id"] = location_id
                location_groups[location_id]["location_name"] = location_name

            location_groups[location_id]["assets"].append({
                "django_id": str(asset.id),
                "name": asset.name,
                "asset_type": (asset.asset_type if asset.asset_type else asset.__class__.__name__),
                "operational_status": asset.operational_status,
                "electrical_system": asset.electrical_system,
            })

        return dict(location_groups)
```

**Notice:**

- All ORM queries in one place
- Optimized with `select_related()`, `prefetch_related()`, `.only()`
- Simple, focused methods
- Returns Django model instances (not serialized data)

---

## Layer 4: Tests (No Database!)

**Rule**: Service tests should use mocks, NOT the database.

### Unit Tests (No DB) vs Integration Tests (With DB)

**Unit Tests** (`test_services.py`):

- ✅ Use `SimpleTestCase` (no DB access)
- ✅ Mock all repository dependencies
- ✅ Test business logic only
- ✅ Fast (milliseconds)

**Integration Tests** (`test_api_schema.py`):

- ✅ Use `APITestCase` with `@pytest.mark.django_db`
- ✅ Test full stack (view → service → repository → DB)
- ✅ Test API contracts
- ✅ Slower (but comprehensive)

### Example: Unit Tests with Mocks

```python
# apps/connections/tests/test_services.py

from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.connections.services import DagService, PowerStatusAnalyzer

class DagServiceUnitTestCase(SimpleTestCase):
    """Unit tests for DagService with mocked repositories (NO DB)."""

    def test_generate_facility_dag_not_found(self):
        """Test DAG generation when facility doesn't exist."""
        # Mock repositories - NO database!
        mock_facility_repo = Mock()
        mock_facility_repo.get_by_id.return_value = None

        service = DagService(Mock(), Mock(), mock_facility_repo, Mock())
        result, status = service.generate_facility_dag("non-existent-id")

        # Assert business logic
        self.assertEqual(status, 404)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Facility not found")

    def test_generate_facility_dag_success(self):
        """Test successful DAG generation with mocked data."""
        # Mock facility
        mock_facility = Mock()
        mock_facility.id = "facility-123"
        mock_facility.name = "Test Facility"

        # Mock repositories
        mock_facility_repo = Mock()
        mock_facility_repo.get_by_id.return_value = mock_facility

        mock_asset_repo = Mock()
        # Create mock assets
        mock_asset1 = Mock()
        mock_asset1.id = "asset-1"
        mock_asset1.name = "UPS-1"
        mock_asset1.asset_type = "UPS"
        mock_asset1.operational_status = "active"
        mock_asset1.location = None

        mock_asset2 = Mock()
        mock_asset2.id = "asset-2"
        mock_asset2.name = "UPS-2"
        mock_asset2.asset_type = "UPS"
        mock_asset2.operational_status = "active"
        mock_asset2.location = None

        mock_asset_repo.get_facility_assets_with_details.return_value = [
            mock_asset1, mock_asset2
        ]
        mock_asset_repo.create_asset_dict.return_value = {
            "asset-1": mock_asset1,
            "asset-2": mock_asset2,
        }

        # Mock connection
        mock_connection = Mock()
        mock_connection.id = "connection-1"
        mock_connection.source_object_id = "asset-1"
        mock_connection.target_object_id = "asset-2"
        mock_connection.connection_type = "electrical"
        mock_connection.notes = None

        mock_connection_repo = Mock()
        mock_connection_repo.get_facility_connections.return_value = [mock_connection]

        # Mock power analyzer
        mock_power_analyzer = Mock()
        mock_power_analyzer.analyze_facility_connections.return_value = {
            "connection-1": True
        }

        # Test service with mocked dependencies
        service = DagService(
            mock_connection_repo, mock_asset_repo,
            mock_facility_repo, mock_power_analyzer
        )
        result, status = service.generate_facility_dag("facility-123")

        # Assert business logic results
        self.assertEqual(status, 200)
        self.assertEqual(result["facility_id"], "facility-123")
        self.assertEqual(result["facility_name"], "Test Facility")
        self.assertEqual(result["total_assets"], 2)
        self.assertEqual(result["total_connections"], 1)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)

    def test_generate_filtered_dag_downstream(self):
        """Test filtered DAG for downstream assets - pure logic test."""
        # Mock facility
        mock_facility = Mock()
        mock_facility.id = "facility-123"
        mock_facility.name = "Test Facility"

        mock_facility_repo = Mock()
        mock_facility_repo.get_by_id.return_value = mock_facility

        # Mock connections in a chain: asset1 -> asset2 -> asset3
        mock_connection1 = Mock()
        mock_connection1.source_object_id = "asset-1"
        mock_connection1.target_object_id = "asset-2"
        mock_connection1.id = "conn-1"
        mock_connection1.connection_type = "electrical"
        mock_connection1.notes = None

        mock_connection2 = Mock()
        mock_connection2.source_object_id = "asset-2"
        mock_connection2.target_object_id = "asset-3"
        mock_connection2.id = "conn-2"
        mock_connection2.connection_type = "electrical"
        mock_connection2.notes = None

        mock_connection_repo = Mock()
        mock_connection_repo.get_facility_connections.return_value = [
            mock_connection1, mock_connection2
        ]

        # Mock assets
        mock_asset_repo = Mock()
        mock_assets = {
            "asset-1": Mock(
                id="asset-1", name="UPS-1", location=None,
                operational_status="active", electrical_system="A"
            ),
            "asset-2": Mock(
                id="asset-2", name="UPS-2", location=None,
                operational_status="active", electrical_system="A"
            ),
            "asset-3": Mock(
                id="asset-3", name="UPS-3", location=None,
                operational_status="active", electrical_system="A"
            ),
        }
        # Add __class__.__name__ attribute
        for asset in mock_assets.values():
            asset.__class__.__name__ = "BaseAsset"

        mock_asset_repo.get_facility_assets_with_details.return_value = list(
            mock_assets.values()
        )
        mock_asset_repo.create_asset_dict.return_value = mock_assets

        mock_power_analyzer = Mock()
        mock_power_analyzer.analyze_facility_connections.return_value = {}

        # Test downstream filtering logic
        service = DagService(
            mock_connection_repo, mock_asset_repo,
            mock_facility_repo, mock_power_analyzer
        )
        result, status = service.generate_filtered_dag(
            "facility-123", downstream_of="asset-1", upstream_of=None
        )

        # Assert filtered results
        self.assertEqual(status, 200)
        # Should include asset-1, asset-2, asset-3 (all downstream of asset-1)
        self.assertEqual(result["total_assets"], 3)
        self.assertIn("filters", result)
        self.assertEqual(result["filters"]["downstream_of"], "asset-1")


class PowerStatusAnalyzerTestCase(SimpleTestCase):
    """Unit tests for PowerStatusAnalyzer - pure logic, no DB."""

    def setUp(self):
        """Set up test data."""
        self.analyzer = PowerStatusAnalyzer()

    def test_extract_power_from_measurements_breaker(self):
        """Test power extraction from breaker measurements."""
        measurements = {
            "equipment_type": "Breaker",
            "active_power_phase_a_kw": 10.0,
            "active_power_phase_b_kw": 15.0,
            "active_power_phase_c_kw": 20.0,
        }

        power = self.analyzer._extract_power_from_measurements(measurements)

        # Should sum all phases and convert kW to W
        self.assertEqual(power, 45000.0)  # (10 + 15 + 20) * 1000

    def test_extract_power_from_measurements_no_data(self):
        """Test power extraction with no measurement data."""
        power = self.analyzer._extract_power_from_measurements(None)
        self.assertEqual(power, 0.0)

        power = self.analyzer._extract_power_from_measurements({})
        self.assertEqual(power, 0.0)

    def test_get_asset_power_by_id_with_data(self):
        """Test getting asset power with measurement data."""
        measurements_data = {
            "asset-123": {
                "equipment_type": "Breaker",
                "active_power_phase_a_kw": 5.0,
                "active_power_phase_b_kw": 5.0,
                "active_power_phase_c_kw": 5.0,
            }
        }

        power = self.analyzer._get_asset_power_by_id("asset-123", measurements_data)

        self.assertEqual(power, 15000.0)  # 15 kW = 15000 W

    def test_get_asset_power_by_id_no_data(self):
        """Test getting asset power with no measurement data."""
        power = self.analyzer._get_asset_power_by_id("asset-123", None)
        self.assertEqual(power, 0.0)

        power = self.analyzer._get_asset_power_by_id("asset-123", {})
        self.assertEqual(power, 0.0)
```

**Benefits of Unit Tests with Mocks:**

- ✅ **Fast**: No database setup/teardown (milliseconds vs seconds)
- ✅ **Isolated**: Tests only business logic, not ORM or DB
- ✅ **Reliable**: No database state pollution between tests
- ✅ **Focused**: Each test targets specific business rules

**When to Use Integration Tests:**

- Testing repository queries (ORM correctness)
- Testing full API endpoints (end-to-end)
- Testing database constraints and migrations
- Testing multi-tenant filtering

---

## Migration Path: Refactoring Existing Apps

### Step-by-Step Process

1. **Create `repositories/` folder** in your app
2. **Extract ORM queries** from views/services into repository classes
3. **Create `services/` folder** (if complex logic exists)
4. **Move business logic** from views into service classes
5. **Update views** to use repositories + services
6. **Write unit tests** with mocks for services
7. **Move old integration tests** to separate file

### Example: Refactoring a ViewSet

**Before (fat view):**

```python
# apps/myapp/api/v1/views.py

class AssetViewSet(viewsets.ModelViewSet):
    def facility_assets(self, request):
        facility_id = request.query_params.get("facility_id")

        # BAD: Direct ORM query in view
        assets = Asset.objects.filter(
            facility_id=facility_id,
            operational_status="active"
        ).select_related("location")

        # BAD: Business logic in view
        result = []
        for asset in assets:
            if asset.calculate_health_score() > 0.8:
                result.append(asset)

        serializer = AssetSerializer(result, many=True)
        return Response(serializer.data)
```

**After (clean architecture):**

```python
# apps/myapp/repositories/asset_repository.py

class AssetRepository:
    def get_facility_assets(self, facility_id: str) -> QuerySet[Asset]:
        return Asset.objects.filter(
            facility_id=facility_id,
            operational_status="active"
        ).select_related("location")


# apps/myapp/services/asset_service.py

class AssetService:
    def __init__(self, asset_repo: AssetRepository):
        self.asset_repo = asset_repo

    def get_healthy_assets(self, facility_id: str, health_threshold: float = 0.8):
        """Business logic: filter assets by health score."""
        assets = self.asset_repo.get_facility_assets(facility_id)
        return [a for a in assets if a.calculate_health_score() > health_threshold]


# apps/myapp/api/v1/views.py

class AssetViewSet(viewsets.ModelViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_repo = AssetRepository()
        self.asset_service = AssetService(self.asset_repo)

    def facility_assets(self, request):
        """THIN wrapper - delegates to service."""
        facility_id = request.query_params.get("facility_id")

        # Delegate to service
        assets = self.asset_service.get_healthy_assets(facility_id)

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)


# apps/myapp/tests/test_asset_service.py

class AssetServiceTestCase(SimpleTestCase):
    """Unit test - no database!"""

    def test_get_healthy_assets(self):
        # Mock repository
        mock_repo = Mock()
        mock_asset1 = Mock()
        mock_asset1.calculate_health_score.return_value = 0.9
        mock_asset2 = Mock()
        mock_asset2.calculate_health_score.return_value = 0.5

        mock_repo.get_facility_assets.return_value = [mock_asset1, mock_asset2]

        # Test service
        service = AssetService(mock_repo)
        result = service.get_healthy_assets("facility-123")

        # Assert business logic
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_asset1)
```

---

## Key Principles Summary

### ✅ DO:

1. **Views**: Thin HTTP wrappers only
2. **Services**: Business logic, no ORM imports
3. **Repositories**: All ORM queries, optimized with `select_related()`
4. **Tests**: Mock repositories for unit tests
5. **Dependency Injection**: Pass repositories to services via constructor
6. **Separation**: Each layer has ONE responsibility

### ❌ DON'T:

1. **Views**: No business logic, no ORM queries
2. **Services**: No `from django.db`, no `.objects.filter()`
3. **Repositories**: No business logic, just data access
4. **Tests**: No database in unit tests (use `SimpleTestCase` + mocks)
5. **Fat Models**: Keep models simple, move logic to services
6. **Mixed Concerns**: Don't blur the lines between layers

---

## Benefits

### 1. **Testability**

- Unit tests run in **milliseconds** (no DB)
- Easy to mock dependencies
- Test business logic in isolation

### 2. **Maintainability**

- Clear separation of concerns
- Easy to find where logic lives
- Refactoring is safer

### 3. **Performance**

- Repository layer can optimize queries
- Easy to add caching at repository level
- Single place to improve query performance

### 4. **Scalability**

- Easy to swap implementations (e.g., switch to different DB)
- Services can be reused across multiple views
- Clear boundaries for team collaboration

---

## FAQ

### Q: Should ALL apps follow this pattern?

**A**: Use judgment. Simple CRUD apps may not need services. But apps with:

- Complex business logic
- Multiple related queries
- Calculations and transformations
- Reusable operations across views

...should absolutely use this pattern.

### Q: Can repositories return dictionaries instead of model instances?

**A**: Prefer returning Django model instances or QuerySets. Only transform to dictionaries in services or serializers. Repositories should stay close to the ORM layer.

### Q: Where do serializers fit?

**A**: Serializers are part of the HTTP layer (with views). They transform service/repository results into API responses. Services should NOT know about serializers.

### Q: What about transactions?

**A**: Handle transactions at the **service layer** using `@transaction.atomic`:

```python
from django.db import transaction

class AssetService:
    @transaction.atomic
    def create_asset_with_connections(self, asset_data, connection_data):
        # All repository calls wrapped in transaction
        asset = self.asset_repo.create(asset_data)
        for conn in connection_data:
            self.connection_repo.create(asset.id, conn)
        return asset
```

### Q: How do I test repositories?

**A**: Repository tests ARE integration tests and should use the database:

```python
from django.test import TestCase

class AssetRepositoryTestCase(TestCase):
    """Integration test - uses DB."""

    def test_get_facility_assets(self):
        facility = Facility.objects.create(name="Test")
        Asset.objects.create(facility=facility, name="Asset 1")

        repo = AssetRepository()
        assets = repo.get_facility_assets(facility.id)

        self.assertEqual(len(assets), 1)
```

---

## Conclusion

The **connections app** demonstrates clean architecture in Django. Use it as a reference when refactoring other apps. The key is **separation of concerns**:

- **Views** = HTTP only
- **Services** = Business logic only
- **Repositories** = Database only
- **Tests** = Mock everything except the database (unit tests) or test full stack (integration tests)

This architecture makes your code **testable, maintainable, and scalable**.
