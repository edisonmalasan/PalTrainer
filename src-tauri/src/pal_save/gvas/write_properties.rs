//! Property-tree writing for GVAS payloads.

use super::model::{
    ArrayValue, BytePropertyValue, MapPropValue, PropertyEntry, PropertyValue, SetValue,
    SetValues, StructValue,
};
use super::writer::FArchiveWriter;

impl FArchiveWriter {
    /// Writes a properties block terminated by the `None` marker.
    pub fn write_properties(&mut self, entries: &[PropertyEntry]) {
        for entry in entries {
            self.write_property(entry);
        }
        self.fstring("None");
    }

    pub fn write_property(&mut self, entry: &PropertyEntry) {
        self.fstring(&entry.name);
        self.fstring(&entry.property.type_name);
        let size_pos = self.position();
        self.write_bytes(&[0u8; 8]);
        let body_start = self.position();
        self.property_value_body(entry);
        // The declared size is the real consumed byte count, which keeps
        // headers consistent even when optional ids are present.
        let declared = (self.position() - body_start) as u64;
        self.patch_u64(size_pos, declared);
    }

    fn property_value_body(&mut self, entry: &PropertyEntry) {
        match &entry.property.value {
            PropertyValue::Struct {
                struct_type,
                struct_id,
                id,
                value,
            } => {
                self.fstring(struct_type);
                self.guid(struct_id);
                self.optional_guid(id.as_ref());
                self.struct_value(struct_type, value);
            }
            PropertyValue::Int { id, value } => {
                self.optional_guid(id.as_ref());
                self.i32(*value);
            }
            PropertyValue::UInt16 { id, value } => {
                self.optional_guid(id.as_ref());
                self.u16(*value);
            }
            PropertyValue::UInt32 { id, value } => {
                self.optional_guid(id.as_ref());
                self.u32(*value);
            }
            PropertyValue::UInt64 { id, value } => {
                self.optional_guid(id.as_ref());
                self.u64(*value);
            }
            PropertyValue::Int64 { id, value } => {
                self.optional_guid(id.as_ref());
                self.i64(*value);
            }
            PropertyValue::FixedPoint64 { id, value } => {
                self.optional_guid(id.as_ref());
                self.i32(*value);
            }
            PropertyValue::Float { id, value } => {
                self.optional_guid(id.as_ref());
                self.f32(*value);
            }
            PropertyValue::Str { id, value } => {
                self.optional_guid(id.as_ref());
                self.fstring(value);
            }
            PropertyValue::Name { id, value } => {
                self.optional_guid(id.as_ref());
                self.fstring(value);
            }
            PropertyValue::Enum { id, enum_type, value } => {
                self.fstring(enum_type);
                self.optional_guid(id.as_ref());
                self.fstring(value);
            }
            // Bool stores its value BEFORE the optional id (mirrors the reader).
            PropertyValue::Bool { id, value } => {
                self.bool(*value);
                self.optional_guid(id.as_ref());
            }
            PropertyValue::Byte { id, enum_type, value } => {
                self.fstring(enum_type);
                self.optional_guid(id.as_ref());
                match value {
                    BytePropertyValue::Byte(b) => self.u8(*b),
                    BytePropertyValue::String(s) => self.fstring(s),
                }
            }
            PropertyValue::Array { id, array_type, value } => {
                self.write_array_property(id.as_ref(), array_type, value);
            }
            PropertyValue::Map(map) => {
                self.fstring(&map.key_type);
                self.fstring(&map.value_type);
                self.optional_guid(map.id.as_ref());
                self.u32(0); // historical padding
                self.u32(map.entries.len() as u32);
                for (k, v) in &map.entries {
                    self.map_prop_value(k, map.key_struct_type.as_deref());
                    self.map_prop_value(v, map.value_struct_type.as_deref());
                }
            }
            PropertyValue::Set(set) => {
                self.write_set_property(set);
            }
        }
    }

    fn write_array_property(
        &mut self,
        id: Option<&super::uuid::PalUuid>,
        array_type: &str,
        value: &ArrayValue,
    ) {
        self.fstring(array_type);
        self.optional_guid(id);
        match value {
            ArrayValue::Struct {
                prop_name,
                prop_type,
                type_name,
                id: element_id,
                values,
            } => {
                self.u32(values.len() as u32);
                self.fstring(prop_name);
                self.fstring(prop_type);
                // Inner declared size: write placeholder, patch after.
                let inner_size_pos = self.position();
                self.write_bytes(&[0u8; 8]);
                let inner_start = self.position();
                self.fstring(type_name);
                self.guid(element_id);
                self.u8(0); // fixed terminator byte
                for sv in values {
                    self.struct_value(type_name, sv);
                }
                let inner_len = (self.position() - inner_start) as u64;
                self.patch_u64(inner_size_pos, inner_len);
            }
            ArrayValue::Bytes(bytes) => {
                self.u32(bytes.len() as u32);
                self.write_bytes(bytes);
            }
            ArrayValue::Ints(v) => {
                self.u32(v.len() as u32);
                for n in v {
                    self.i32(*n);
                }
            }
            ArrayValue::UInt32s(v) => {
                self.u32(v.len() as u32);
                for n in v {
                    self.u32(*n);
                }
            }
            ArrayValue::Int64s(v) => {
                self.u32(v.len() as u32);
                for n in v {
                    self.i64(*n);
                }
            }
            ArrayValue::Floats(v) => {
                self.u32(v.len() as u32);
                for n in v {
                    self.f32(*n);
                }
            }
            ArrayValue::Strings(v) => {
                self.u32(v.len() as u32);
                for s in v {
                    self.fstring(s);
                }
            }
            ArrayValue::Bools(v) => {
                self.u32(v.len() as u32);
                for b in v {
                    self.bool(*b);
                }
            }
        }
    }

    fn write_set_property(&mut self, set: &SetValue) {
        self.fstring(&set.set_type);
        self.optional_guid(set.id.as_ref());
        self.u32(0); // historical padding
        match &set.values {
            SetValues::Struct(items) => {
                self.u32(items.len() as u32);
                let st = set.struct_type.as_deref().unwrap_or("StructProperty");
                for sv in items {
                    self.struct_value(st, sv);
                }
            }
            SetValues::Properties(items) => {
                self.u32(items.len() as u32);
                for props in items {
                    self.write_properties(props);
                }
            }
        }
    }

    fn map_prop_value(&mut self, value: &MapPropValue, struct_type: Option<&str>) {
        match value {
            MapPropValue::Struct(sv) => {
                let st = struct_type.unwrap_or("StructProperty");
                self.struct_value(st, sv);
            }
            MapPropValue::Enum(s) | MapPropValue::Name(s) | MapPropValue::Str(s) => {
                self.fstring(s);
            }
            MapPropValue::Int(n) => self.i32(*n),
            MapPropValue::Bool(b) => self.bool(*b),
            MapPropValue::UInt32(n) => self.u32(*n),
            MapPropValue::Int64(n) => self.i64(*n),
        }
    }

    fn struct_value(&mut self, struct_type: &str, value: &StructValue) {
        match value {
            StructValue::Vector { x, y, z } => {
                self.f64(*x);
                self.f64(*y);
                self.f64(*z);
            }
            StructValue::DateTime(v) => self.u64(*v),
            StructValue::Guid(g) => self.guid(g),
            StructValue::Quat { x, y, z, w } => {
                self.f64(*x);
                self.f64(*y);
                self.f64(*z);
                self.f64(*w);
            }
            StructValue::LinearColor { r, g, b, a } => {
                self.f32(*r);
                self.f32(*g);
                self.f32(*b);
                self.f32(*a);
            }
            // Disk order is BGRA (mirrors the reader).
            StructValue::Color { b, g, r, a } => {
                self.u8(*b);
                self.u8(*g);
                self.u8(*r);
                self.u8(*a);
            }
            StructValue::Properties(props) => {
                let _ = struct_type; // generic structs use the property list
                self.write_properties(props);
            }
        }
    }
}
