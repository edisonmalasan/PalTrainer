from __future__ import annotations

import pytest
from tests.dynamic_importer import import_from

FArchiveWriter = import_from('palsav.archive', 'FArchiveWriter')
FArchiveReader = import_from('palsav.archive', 'FArchiveReader')
UUID = import_from('palsav.archive', 'UUID')

map_concrete_model = import_from('palsav.rawdata.map_concrete_model')
group = import_from('palsav.rawdata.group')
character = import_from('palsav.rawdata.character')


def _zero_uuid() -> UUID:
    return UUID(bytes(range(16)))


def _uuid(seed: int) -> UUID:
    return UUID(bytes(((seed + i) & 0xFF) for i in range(16)))


class TestItemBooth:
    """Characterizes PalMapObjectItemBoothModel lock-flag preservation."""

    def _build(self, is_private_lock: int) -> bytes:
        writer = FArchiveWriter()
        writer.guid(_uuid(1))            # instance_id
        writer.guid(_uuid(2))            # model_instance_id
        writer.write(b'\x00\x00\x00\x00')  # leading_bytes (4)
        writer.guid(_uuid(3))            # private_lock_player_uid
        writer.u32(0)                     # trade_infos (empty tarray)
        writer.write(b'\x00' * 12)        # unknown_before_lock
        writer.byte(is_private_lock)      # is_private_lock
        writer.write(b'\x00' * 7)         # unknown_after_lock
        return writer.bytes()

    def test_item_booth_roundtrip_preserves_bytes(self):
        original = self._build(is_private_lock=1)
        reader = FArchiveReader(b'')
        decoded = map_concrete_model.decode_bytes(reader, list(original), 'itembooth')
        assert decoded['concrete_model_type'] == 'PalMapObjectItemBoothModel'
        assert decoded['is_private_lock'] == 1
        reencoded = map_concrete_model.encode_bytes(decoded)
        assert reencoded == original

    def test_item_booth_lock_flag_roundtrip(self):
        original = self._build(is_private_lock=0)
        reader = FArchiveReader(b'')
        decoded = map_concrete_model.decode_bytes(reader, list(original), 'itembooth')
        assert decoded['is_private_lock'] == 0
        assert map_concrete_model.encode_bytes(decoded) == original


class TestPalBooth:
    """Characterizes PalMapObjectPalBoothModel lock-flag preservation."""

    def _build(self, is_private_lock: int) -> bytes:
        writer = FArchiveWriter()
        writer.guid(_uuid(1))            # instance_id
        writer.guid(_uuid(2))            # model_instance_id
        writer.write(b'\x00\x00\x00\x00')  # leading_bytes (4)
        writer.write(b'\x00' * 224)       # unknown_prefix
        writer.write(b'\x00' * 6)         # unknown_mid
        writer.byte(is_private_lock)      # is_private_lock (byte 224)
        writer.write(b'\x00' * 11)        # trailing_bytes
        return writer.bytes()

    def test_pal_booth_roundtrip_preserves_bytes(self):
        original = self._build(is_private_lock=1)
        reader = FArchiveReader(b'')
        decoded = map_concrete_model.decode_bytes(reader, list(original), 'palbooth')
        assert decoded['concrete_model_type'] == 'PalMapObjectPalBoothModel'
        assert decoded['is_private_lock'] == 1
        assert map_concrete_model.encode_bytes(decoded) == original

    def test_pal_booth_lock_flag_roundtrip(self):
        original = self._build(is_private_lock=0)
        reader = FArchiveReader(b'')
        decoded = map_concrete_model.decode_bytes(reader, list(original), 'palbooth')
        assert decoded['is_private_lock'] == 0
        assert map_concrete_model.encode_bytes(decoded) == original


class TestGuildV1:
    """Characterizes pre-update (v1) guild binary roundtrip."""

    def _build(self) -> bytes:
        writer = FArchiveWriter()
        writer.guid(_zero_uuid())                 # group_id
        writer.fstring('GuildA')                  # group_name
        writer.u32(0)                             # handles (empty)
        writer.byte(1)                            # org_type (Guild)
        writer.write(b'\x00\x00\x00\x00')          # leading_bytes (4)
        writer.u32(0)                             # base_ids (empty)
        writer.i32(0)                             # unknown_1
        writer.i32(1)                             # base_camp_level
        writer.u32(0)                             # base camp points (empty)
        writer.fstring('GuildA')                  # guild_name
        writer.guid(_zero_uuid())                 # last_guild_name_modifier_player_uid
        writer.u32(0)                             # guild_markers (empty)
        # v1 tail
        writer.guid(_zero_uuid())                 # admin_player_uid
        writer.u32(0)                             # players (empty)
        writer.write(b'\x00\x00\x00\x00')          # trailing_bytes (4)
        return writer.bytes()

    def test_guild_v1_roundtrip_preserves_bytes(self):
        original = self._build()
        reader = FArchiveReader(b'')
        decoded = group.decode_bytes(reader, list(original), 'EPalGroupType::Guild')
        assert decoded['group_type'] == 'EPalGroupType::Guild'
        assert decoded['guild_name'] == 'GuildA'
        assert decoded['base_camp_level'] == 1
        reencoded = group.encode_bytes(decoded)
        assert reencoded == original


class TestGuildV2:
    """Characterizes post-Sakurajima (v2) guild tail with roles/permissions."""

    def _build(self) -> bytes:
        writer = FArchiveWriter()
        writer.guid(_zero_uuid())                 # group_id
        writer.fstring('GuildB')                  # group_name
        writer.u32(0)                             # handles (empty)
        writer.byte(1)                            # org_type (Guild)
        writer.write(b'\x00\x00\x00\x00')          # leading_bytes (4)
        writer.u32(0)                             # base_ids (empty)
        writer.i32(0)                             # unknown_1
        writer.i32(1)                             # base_camp_level
        writer.u32(0)                             # base camp points (empty)
        writer.fstring('GuildB')                  # guild_name
        writer.guid(_zero_uuid())                 # last_guild_name_modifier_player_uid
        writer.u32(0)                             # guild_markers (empty)
        # v2 tail
        writer.u32(1)                             # guild_chest_allowed_roles
        writer.byte(1)
        writer.i32(0)                             # unknown_i32
        writer.guid(_zero_uuid())                 # admin_player_uid
        writer.u32(1)                             # players
        writer.guid(_uuid(10))                    # player_uid
        writer.i64(1234567890)                    # last_online_real_time
        writer.fstring('Player1')                 # player_name
        writer.byte(1)                            # role (admin)
        writer.u32(1)                             # role_permissions
        writer.byte(1)                            # role
        writer.u32(2)                             # permissions
        writer.byte(1)
        writer.byte(2)
        writer.write(b'\x00\x00\x00\x00')          # trailing_bytes (4)
        return writer.bytes()

    def test_guild_v2_roundtrip_preserves_bytes(self):
        original = self._build()
        reader = FArchiveReader(b'')
        decoded = group.decode_bytes(reader, list(original), 'EPalGroupType::Guild')
        assert decoded['group_type'] == 'EPalGroupType::Guild'
        assert decoded['guild_name'] == 'GuildB'
        assert decoded['role_permissions'][0]['role'] == 1
        assert decoded['players'][0]['role'] == 1
        reencoded = group.encode_bytes(decoded)
        assert reencoded == original


class TestOpaqueProperties:
    """Characterizes unknown-property and trailing-byte preservation."""

    def test_unknown_map_object_concrete_model_is_opaque(self):
        payload = bytes(range(64))
        reader = FArchiveReader(b'')
        decoded = map_concrete_model.decode_bytes(reader, list(payload), 'totally-unknown-model')
        assert decoded == {'values': list(payload)}

    def test_character_trailing_unknown_bytes_preserved(self):
        writer = FArchiveWriter()
        writer.fstring('None')                    # empty object property stream
        writer.write(b'\xde\xad\xbe\xef')          # unknown_bytes (4)
        writer.guid(_uuid(7))                     # group_id
        writer.write(b'\x00\x00\x00\x00')          # trailing_bytes (4)
        writer.write(b'\x99\x98\x97\x96\x95')      # trailing_unknown_bytes
        payload = writer.bytes()
        reader = FArchiveReader(b'')
        decoded = character.decode_bytes(reader, list(payload))
        assert decoded['trailing_unknown_bytes'] == b'\x99\x98\x97\x96\x95'
        assert character.encode_bytes(decoded) == payload