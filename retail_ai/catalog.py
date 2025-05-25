from pathlib import Path
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import NotFound
from databricks.sdk.service.catalog import (
    CatalogInfo,
    SchemaInfo,
    VolumeInfo,
    VolumeType,
)


def _volume_as_path(self: VolumeInfo) -> Path:
    """
    Convert a Databricks Volume to a filesystem-like Path object.

    This helper method adds the as_path() functionality to the VolumeInfo class
    through monkey patching, allowing volumes to be referenced with standard
    Python Path operations.

    Args:
        self: The VolumeInfo instance

    Returns:
        A Path object representing the volume's location in the Databricks filesystem
    """
    return Path(f"/Volumes/{self.catalog_name}/{self.schema_name}/{self.name}")


# Monkey patch the VolumeInfo class to add the as_path method
VolumeInfo.as_path = _volume_as_path


def full_name(entity: str, catalog: dict[str, Any]) -> str:
    """
    Generate the full name of an entity in the format `catalog.schema.entity`.

    Args:
        entity: The name of the entity (e.g., table, view).
        catalog: A dictionary containing catalog information with keys:
            - "catalog_name": Name of the catalog.
            - "schema_name": Name of the schema.

    Returns:
        A string representing the full name of the entity.
    """
    if catalog:
        if "full_name" in catalog:
            return f"{catalog['full_name']}.{entity}"
        if "catalog_name" in catalog and "schema_name" in catalog:
            return f"{catalog['catalog_name']}.{catalog['schema_name']}.{entity}"
    else:
        return entity


def get_or_create_catalog(name: str, w: WorkspaceClient | None = None) -> CatalogInfo:
    """
    Get an existing catalog or create a new one if it doesn't exist.

    This function provides idempotent catalog creation for Unity Catalog,
    ensuring the requested catalog is available regardless of whether it
    already exists.

    Args:
        name: The name of the catalog to get or create
        w: Optional WorkspaceClient instance (creates one if not provided)

    Returns:
        CatalogInfo object representing the requested catalog
    """
    if w is None:
        w = WorkspaceClient()

    catalog: CatalogInfo
    try:
        # Try to fetch the existing catalog
        catalog = w.catalogs.get(name=name)
    except NotFound:
        # Create the catalog if it doesn't exist
        catalog = w.catalogs.create(name=name)
    return catalog


def get_or_create_database(
    catalog: CatalogInfo, name: str, w: WorkspaceClient | None = None
) -> SchemaInfo:
    """
    Get an existing database (schema) or create a new one if it doesn't exist.

    Provides idempotent database creation within a Unity Catalog catalog.
    In Databricks, databases are also referred to as schemas.

    Args:
        catalog: The catalog object where the database should exist
        name: The name of the database to get or create
        w: Optional WorkspaceClient instance (creates one if not provided)

    Returns:
        SchemaInfo object representing the requested database/schema
    """
    if w is None:
        w = WorkspaceClient()

    database: SchemaInfo
    try:
        # Try to fetch the existing database using its fully qualified name
        database = w.schemas.get(full_name=f"{catalog.name}.{name}")
    except NotFound:
        # Create the database if it doesn't exist
        database = w.schemas.create(name=name, catalog_name=catalog.name)
    return database


def get_or_create_volume(
    catalog: CatalogInfo,
    database: SchemaInfo,
    name: str,
    volume_type: VolumeType = VolumeType.MANAGED,
    w: WorkspaceClient | None = None,
) -> VolumeInfo:
    """
    Get an existing volume or create a new one if it doesn't exist.

    Provides idempotent volume creation within a Unity Catalog database.
    Volumes are used to store files and can be mounted like file systems.

    Args:
        catalog: The catalog object where the volume should exist
        database: The database/schema object where the volume should exist
        name: The name of the volume to get or create
        volume_type: The type of volume (MANAGED or EXTERNAL)
        w: Optional WorkspaceClient instance (creates one if not provided)

    Returns:
        VolumeInfo object representing the requested volume
    """
    if w is None:
        w = WorkspaceClient()

    volume: VolumeInfo
    try:
        # Try to fetch the existing volume using its fully qualified name
        volume = w.volumes.read(name=f"{database.full_name}.{name}")
    except NotFound:
        # Create the volume if it doesn't exist
        volume = w.volumes.create(
            catalog_name=catalog.name,
            schema_name=database.name,
            name=name,
            volume_type=VolumeType.MANAGED,
        )
    return volume
