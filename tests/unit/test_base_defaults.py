from core.base import DataModelBase


def test_datamodelbase_defaults_and_relations_indexes():
    class M(DataModelBase):
        pass

    assert isinstance(M.searchable_fields, list)
    assert isinstance(M.sortable_fields, list)
    assert M.relations() == []
    assert M.indexes() == []

