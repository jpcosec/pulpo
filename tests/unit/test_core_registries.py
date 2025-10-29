from pydantic import BaseModel

from core.registries import ModelInfo, ModelRegistry, OperationMetadata, OperationRegistry


def test_model_registry_register_and_get_and_clear():
    ModelRegistry.clear()
    info = ModelInfo(name="Foo", document_cls=object)
    ModelRegistry.register(info)

    got = ModelRegistry.get("Foo")
    assert got is not None
    assert got.name == "Foo"
    assert len(ModelRegistry.list_all()) == 1

    ModelRegistry.clear()
    assert ModelRegistry.get("Foo") is None


class In(BaseModel):
    a: int


class Out(BaseModel):
    b: int


async def dummy(_: In) -> Out:  # pragma: no cover - not executed here
    return Out(b=1)


def test_operation_registry_register_and_get_and_clear():
    OperationRegistry.clear()
    meta = OperationMetadata(
        name="op1",
        description="d",
        category="test",
        input_schema=In,
        output_schema=Out,
        function=dummy,
    )
    OperationRegistry.register(meta)

    got = OperationRegistry.get("op1")
    assert got is not None
    assert got.name == "op1"
    assert len(OperationRegistry.list_all()) == 1

    OperationRegistry.clear()
    assert OperationRegistry.get("op1") is None

