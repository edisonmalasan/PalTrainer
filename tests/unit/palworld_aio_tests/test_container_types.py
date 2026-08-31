from __future__ import annotations
import io
import uuid
from tests.dynamic_importer import import_from

ct = import_from('palworld_xgp_import.container_types')

FILETIME = ct.FILETIME
Container = ct.Container
ContainerIndex = ct.ContainerIndex
ContainerError = ct.ContainerError


def test_filetime_roundtrip():
    ft = FILETIME.from_timestamp(1700000000.0)
    raw = ft.to_bytes()
    restored = FILETIME.from_stream(io.BytesIO(raw))
    assert abs(restored.to_timestamp() - 1700000000.0) < 0.001


def test_filetime_comparisons():
    a = FILETIME.from_timestamp(1000.0)
    b = FILETIME.from_timestamp(2000.0)
    assert a < b
    assert b > a
    assert a == a
    assert a <= b
    assert b >= a
    assert a != b


def test_filetime_far_future():
    ft = FILETIME.far_future()
    assert ft.to_timestamp() > 4100000000.0


def test_container_roundtrip():
    cid = uuid.uuid4()
    ft = FILETIME.from_timestamp(1700000000.0)
    c = Container(container_name='TestSave-Level', cloud_id='', seq=1, flag=4, container_uuid=cid, mtime=ft, size=4096)
    raw = c.to_bytes()
    restored = Container.from_stream(io.BytesIO(raw))
    assert restored.container_name == 'TestSave-Level'
    assert restored.seq == 1
    assert restored.container_uuid == cid
    assert restored.size == 4096


def test_container_index_get_save_containers():
    ft = FILETIME.from_timestamp(1700000000.0)
    containers = [
        Container(container_name='World1-Level', cloud_id='', seq=1, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
        Container(container_name='World1-LevelMeta', cloud_id='', seq=1, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
        Container(container_name='World1-LocalData', cloud_id='', seq=1, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
        Container(container_name='World1-Level', cloud_id='', seq=2, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
        Container(container_name='OtherSave-Level', cloud_id='', seq=1, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
    ]
    idx = ContainerIndex(flag1=0, package_name='Test', mtime=ft, flag2=0, index_uuid='idx', unknown=0, containers=containers)
    result = idx.get_save_containers('World1')
    assert 'Level' in result
    assert result['Level'].seq == 2
    assert 'LevelMeta' in result
    assert 'LocalData' in result
    assert 'OtherSave-Level' not in result


def test_container_index_roundtrip():
    ft = FILETIME.from_timestamp(1700000000.0)
    containers = [
        Container(container_name='Test-Level', cloud_id='', seq=1, flag=4, container_uuid=uuid.uuid4(), mtime=ft, size=100),
    ]
    idx = ContainerIndex(flag1=0, package_name='MyPackage', mtime=ft, flag2=0, index_uuid='my-uuid', unknown=0, containers=containers)
    assert idx.get_save_containers('NonExistent') == {}


def test_container_index_rejects_unknown_version():
    buf = io.BytesIO(bytes([0xFF, 0, 0, 0]))
    import pytest
    with pytest.raises(ContainerError, match='unsupported container index version'):
        ct.ContainerIndex.from_stream(buf)