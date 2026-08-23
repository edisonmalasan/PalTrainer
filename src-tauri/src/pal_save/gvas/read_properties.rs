//! Property-tree reading for GVAS payloads.

use crate::error::SaveError;

use super::model::{
    ArrayValue, BytePropertyValue, MapPropValue, MapValue, Property, PropertyEntry, PropertyValue,
    SetValue, SetValues, StructValue,
};
use super::reader::FArchiveReader;

impl FArchiveReader<'_> {
    /// Reads properties until the `None` terminator.
    pub fn properties_until_end(&mut self, path: &str) -> Result<Vec<PropertyEntry>, SaveError> {
        let mut entries = Vec::new();
        loop {
            let name = self.fstring()?;
            if name == "None" {
                break;
            }
            let type_name = self.fstring()?;
            // The declared size is not needed for decoding because type
            // dispatch is authoritative; the writer recomputes sizes.
            let _declared_size = self.u64()?;
            let property = self.property(&type_name, &format!("{path}.{name}"))?;
            entries.push(PropertyEntry { name, property });
        }
        Ok(entries)
    }

    pub fn property(&mut self, type_name: &str, path: &str) -> Result<Property, SaveError> {
        let value = self.property_value(type_name, path)?;
        Ok(Property {
            type_name: type_name.to_string(),
            custom_type: None,
            value,
        })
    }

    /// Type-dispatched property body. Path-keyed custom codecs hook in
    /// here in a later phase.
    pub(crate) fn property_value(
        &mut self,
        type_name: &str,
        path: &str,
    ) -> Result<PropertyValue, SaveError> {
        match type_name {
            "StructProperty" => self.struct_property(path),
            "IntProperty" => Ok(PropertyValue::Int {
                id: self.optional_guid()?,
                value: self.i32()?,
            }),
            "UInt16Property" => Ok(PropertyValue::UInt16 {
                id: self.optional_guid()?,
                value: self.u16()?,
            }),
            "UInt32Property" => Ok(PropertyValue::UInt32 {
                id: self.optional_guid()?,
                value: self.u32()?,
            }),
            "UInt64Property" => Ok(PropertyValue::UInt64 {
                id: self.optional_guid()?,
                value: self.u64()?,
            }),
            "Int64Property" => Ok(PropertyValue::Int64 {
                id: self.optional_guid()?,
                value: self.i64()?,
            }),
            "FixedPoint64Property" => Ok(PropertyValue::FixedPoint64 {
                id: self.optional_guid()?,
                value: self.i32()?,
            }),
            "FloatProperty" => Ok(PropertyValue::Float {
                id: self.optional_guid()?,
                value: self.f32()?,
            }),
            "StrProperty" => Ok(PropertyValue::Str {
                id: self.optional_guid()?,
                value: self.fstring()?,
            }),
            "NameProperty" => Ok(PropertyValue::Name {
                id: self.optional_guid()?,
                value: self.fstring()?,
            }),
            "EnumProperty" => {
                let enum_type = self.fstring()?;
                let id = self.optional_guid()?;
                let value = self.fstring()?;
                Ok(PropertyValue::Enum {
                    id,
                    enum_type,
                    value,
                })
            }
            // Bool stores its value BEFORE the optional id, unlike the rest.
            "BoolProperty" => {
                let value = self.bool()?;
                let id = self.optional_guid()?;
                Ok(PropertyValue::Bool { id, value })
            }
            "ByteProperty" => {
                let enum_type = self.fstring()?;
                let id = self.optional_guid()?;
                let value = if enum_type == "None" {
                    BytePropertyValue::Byte(self.u8()?)
                } else {
                    BytePropertyValue::String(self.fstring()?)
                };
                Ok(PropertyValue::Byte {
                    id,
                    enum_type,
                    value,
                })
            }
            "ArrayProperty" => self.array_property(path),
            "MapProperty" => self.map_property(path),
            "SetProperty" => self.set_property(path),
            other => Err(SaveError::UnknownPropertyType {
                type_name: other.to_string(),
                path: path.to_string(),
            }),
        }
    }

    pub(crate) fn struct_property(&mut self, path: &str) -> Result<PropertyValue, SaveError> {
        let struct_type = self.fstring()?;
        let struct_id = self.guid()?;
        let id = self.optional_guid()?;
        let value = self.struct_value(&struct_type, path)?;
        Ok(PropertyValue::Struct {
            struct_type,
            struct_id,
            id,
            value: Box::new(value),
        })
    }

    /// Reads a struct body according to its declared type name; unknown
    /// types fall back to a nested properties block.
    pub fn struct_value(
        &mut self,
        struct_type: &str,
        path: &str,
    ) -> Result<StructValue, SaveError> {
        match struct_type {
            "Vector" => Ok(StructValue::Vector {
                x: self.f64()?,
                y: self.f64()?,
                z: self.f64()?,
            }),
            "DateTime" => Ok(StructValue::DateTime(self.u64()?)),
            "Guid" => Ok(StructValue::Guid(self.guid()?)),
            "Quat" => Ok(StructValue::Quat {
                x: self.f64()?,
                y: self.f64()?,
                z: self.f64()?,
                w: self.f64()?,
            }),
            "LinearColor" => Ok(StructValue::LinearColor {
                r: self.f32()?,
                g: self.f32()?,
                b: self.f32()?,
                a: self.f32()?,
            }),
            // Note the byte order: BGRA on disk.
            "Color" => Ok(StructValue::Color {
                b: self.u8()?,
                g: self.u8()?,
                r: self.u8()?,
                a: self.u8()?,
            }),
            _ => Ok(StructValue::Properties(self.properties_until_end(path)?)),
        }
    }

    fn array_property(&mut self, path: &str) -> Result<PropertyValue, SaveError> {
        let array_type = self.fstring()?;
        let id = self.optional_guid()?;
        let count = self.u32()?;

        if array_type == "StructProperty" {
            let prop_name = self.fstring()?;
            let prop_type = self.fstring()?;
            // Inner declared size; recomputed by the writer.
            let _declared_size = self.u64()?;
            let type_name = self.fstring()?;
            let element_id = self.guid()?;
            self.u8()?; // fixed terminator byte, always zero
            let inner_path = format!("{path}.{prop_name}");
            let mut values = Vec::with_capacity(count.min(4096) as usize);
            for _ in 0..count {
                values.push(self.struct_value(&type_name, &inner_path)?);
            }
            return Ok(PropertyValue::Array {
                id,
                array_type,
                value: ArrayValue::Struct {
                    prop_name,
                    prop_type,
                    type_name,
                    id: element_id,
                    values,
                },
            });
        }

        if array_type == "ByteProperty" {
            let bytes = self.take(count as usize)?.to_vec();
            return Ok(PropertyValue::Array {
                id,
                array_type,
                value: ArrayValue::Bytes(bytes),
            });
        }

        let mut ints = Vec::new();
        let mut uints = Vec::new();
        let mut int64s = Vec::new();
        let mut floats = Vec::new();
        let mut strings = Vec::new();
        let mut bools = Vec::new();
        for _ in 0..count {
            match array_type.as_str() {
                "IntProperty" => ints.push(self.i32()?),
                "UInt32Property" => uints.push(self.u32()?),
                "Int64Property" => int64s.push(self.i64()?),
                "FloatProperty" => floats.push(self.f32()?),
                "StrProperty" | "NameProperty" | "EnumProperty" => strings.push(self.fstring()?),
                "BoolProperty" => bools.push(self.bool()?),
                other => {
                    return Err(SaveError::UnknownArrayType {
                        array_type: other.to_string(),
                        path: path.to_string(),
                    });
                }
            }
        }
        let value = match array_type.as_str() {
            "IntProperty" => ArrayValue::Ints(ints),
            "UInt32Property" => ArrayValue::UInt32s(uints),
            "Int64Property" => ArrayValue::Int64s(int64s),
            "FloatProperty" => ArrayValue::Floats(floats),
            "BoolProperty" => ArrayValue::Bools(bools),
            _ => ArrayValue::Strings(strings),
        };
        Ok(PropertyValue::Array {
            id,
            array_type,
            value,
        })
    }

    fn map_property(&mut self, path: &str) -> Result<PropertyValue, SaveError> {
        let key_type = self.fstring()?;
        let value_type = self.fstring()?;
        let id = self.optional_guid()?;
        self.u32()?; // historical padding, always zero in practice
        let count = self.u32()?;

        let key_struct_type = if key_type == "StructProperty" {
            Some(self.type_or(&format!("{path}.Key"), "Guid"))
        } else {
            None
        };
        let value_struct_type = if value_type == "StructProperty" {
            Some(self.type_or(&format!("{path}.Value"), "StructProperty"))
        } else {
            None
        };

        let mut entries = Vec::with_capacity(count.min(4096) as usize);
        for _ in 0..count {
            let key = self.map_prop_value(
                &key_type,
                key_struct_type.as_deref(),
                &format!("{path}.Key"),
            )?;
            let value = self.map_prop_value(
                &value_type,
                value_struct_type.as_deref(),
                &format!("{path}.Value"),
            )?;
            entries.push((key, value));
        }

        Ok(PropertyValue::Map(Box::new(MapValue {
            key_type,
            value_type,
            key_struct_type,
            value_struct_type,
            id,
            entries,
        })))
    }

    fn set_property(&mut self, path: &str) -> Result<PropertyValue, SaveError> {
        let set_type = self.fstring()?;
        let id = self.optional_guid()?;
        self.u32()?; // historical padding, always zero in practice
        let count = self.u32()?;

        let struct_type = if set_type == "StructProperty" {
            Some(self.type_or(&format!("{path}.StructProperty"), "StructProperty"))
        } else {
            None
        };

        let element_path = format!("{path}.StructProperty");
        let values = if set_type == "StructProperty" && struct_type.is_some() {
            let st = struct_type.clone().expect("checked above");
            let mut items = Vec::with_capacity(count.min(4096) as usize);
            for _ in 0..count {
                items.push(self.struct_value(&st, &element_path)?);
            }
            SetValues::Struct(items)
        } else {
            let mut items = Vec::with_capacity(count.min(4096) as usize);
            for _ in 0..count {
                items.push(self.properties_until_end(path)?);
            }
            SetValues::Properties(items)
        };

        Ok(PropertyValue::Set(Box::new(SetValue {
            set_type,
            struct_type,
            id,
            values,
        })))
    }

    fn map_prop_value(
        &mut self,
        type_name: &str,
        struct_type: Option<&str>,
        path: &str,
    ) -> Result<MapPropValue, SaveError> {
        match type_name {
            "StructProperty" => {
                let st = struct_type.unwrap_or("StructProperty");
                Ok(MapPropValue::Struct(Box::new(self.struct_value(st, path)?)))
            }
            "EnumProperty" => Ok(MapPropValue::Enum(self.fstring()?)),
            "NameProperty" => Ok(MapPropValue::Name(self.fstring()?)),
            "IntProperty" => Ok(MapPropValue::Int(self.i32()?)),
            "BoolProperty" => Ok(MapPropValue::Bool(self.bool()?)),
            "UInt32Property" => Ok(MapPropValue::UInt32(self.u32()?)),
            "StrProperty" => Ok(MapPropValue::Str(self.fstring()?)),
            "Int64Property" => Ok(MapPropValue::Int64(self.i64()?)),
            other => Err(SaveError::UnknownPropertyType {
                type_name: other.to_string(),
                path: path.to_string(),
            }),
        }
    }
}
