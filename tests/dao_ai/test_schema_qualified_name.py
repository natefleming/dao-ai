"""Unit tests for the shared ``HasSchemaQualifiedName.full_name`` derivation."""

import pytest

from dao_ai.config import (
    EvaluationDatasetModel,
    FunctionModel,
    HasSchemaQualifiedName,
    IndexModel,
    InferenceEndpointModel,
    RegisteredModelModel,
    TableModel,
    VolumeModel,
)

SCHEMA = {"catalog_name": "cat", "schema_name": "sch"}

SCHEMA_QUALIFIED_MODELS = [
    TableModel,
    FunctionModel,
    IndexModel,
    VolumeModel,
    InferenceEndpointModel,
    RegisteredModelModel,
    EvaluationDatasetModel,
]


@pytest.mark.unit
@pytest.mark.parametrize("model_cls", SCHEMA_QUALIFIED_MODELS)
def test_uses_shared_full_name(model_cls):
    assert issubclass(model_cls, HasSchemaQualifiedName)
    assert "full_name" not in model_cls.__dict__


@pytest.mark.unit
@pytest.mark.parametrize("model_cls", SCHEMA_QUALIFIED_MODELS)
def test_schema_and_name_give_three_level_name(model_cls):
    assert model_cls(schema=SCHEMA, name="obj").full_name == "cat.sch.obj"


@pytest.mark.unit
@pytest.mark.parametrize("model_cls", SCHEMA_QUALIFIED_MODELS)
def test_name_without_schema_is_verbatim(model_cls):
    assert model_cls(name="a.b.obj").full_name == "a.b.obj"


@pytest.mark.unit
@pytest.mark.parametrize("model_cls", [TableModel, FunctionModel])
def test_schema_without_name_gives_schema_name(model_cls):
    assert model_cls(schema=SCHEMA).full_name == "cat.sch"
