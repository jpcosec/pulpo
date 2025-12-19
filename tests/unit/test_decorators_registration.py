from pydantic import BaseModel

from core import datamodel, operation
from core.analysis.registries import ModelRegistry, OperationRegistry


def test_datamodel_decorator_registers_class():
    ModelRegistry.clear()

    @datamodel(name="MyModel", tags=["t1"])  # type: ignore
    class Dummy:
        searchable_fields = ["a"]
        sortable_fields = ["b"]

        @classmethod
        def relations(cls):
            return [{"name": "rels", "target": "Other", "cardinality": "many"}]

    info = ModelRegistry.get("MyModel")
    assert info is not None
    assert info.name == "MyModel"
    assert info.searchable_fields == ["a"]
    assert info.sortable_fields == ["b"]
    assert info.relations and info.relations[0]["target"] == "Other"


def test_operation_decorator_registers_function_and_class():
    OperationRegistry.clear()

    class In(BaseModel):
        a: int

    class Out(BaseModel):
        b: int

    @operation(
        name="f_op",
        description="f",
        category="test",
        inputs=In,
        outputs=Out,
        models_in=["A"],
        models_out=["B"],
        stage="s",
    )
    async def f(_: In) -> Out:  # pragma: no cover - not executed here
        return Out(b=1)

    @operation(
        name="c_op",
        description="c",
        category="test",
        inputs=In,
        outputs=Out,
    )
    class C:
        async def run(self, _: In) -> Out:  # pragma: no cover - not executed here
            return Out(b=2)

    names = {op.name for op in OperationRegistry.list_all()}
    assert {"f_op", "c_op"}.issubset(names)

