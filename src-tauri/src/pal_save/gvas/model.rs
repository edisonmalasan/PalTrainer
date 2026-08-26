//! Typed GVAS property tree.
//!
//! Mirrors the reference tool's decoded structure: an ordered list of
//! named properties whose values are tagged unions. Order preservation is
//! required for byte-perfect roundtrips.

use super::uuid::PalUuid;

/// One named property inside a properties block.
#[derive(Clone, Debug, PartialEq)]
pub struct PropertyEntry {
    pub name: String,
    pub property: Property,
}

#[derive(Clone, Debug, PartialEq)]
pub struct Property {
    /// UE type name, e.g. `IntProperty` or `StructProperty`.
    pub type_name: String,
    /// Path key of the custom codec that produced this value, if any.
    pub custom_type: Option<String>,
    pub value: PropertyValue,
}

impl Property {
    pub fn new(type_name: impl Into<String>, value: PropertyValue) -> Self {
        Self {
            type_name: type_name.into(),
            custom_type: None,
            value,
        }
    }
}

/// A nested struct payload; the variant selects the fixed binary layout.
#[derive(Clone, Debug, PartialEq)]
pub enum StructValue {
    Vector {
        x: f64,
        y: f64,
        z: f64,
    },
    DateTime(u64),
    Guid(PalUuid),
    Quat {
        x: f64,
        y: f64,
        z: f64,
        w: f64,
    },
    LinearColor {
        r: f32,
        g: f32,
        b: f32,
        a: f32,
    },
    Color {
        b: u8,
        g: u8,
        r: u8,
        a: u8,
    },
    /// Generic struct: a full nested properties block ending with `None`.
    Properties(Vec<PropertyEntry>),
}

#[derive(Clone, Debug, PartialEq)]
pub enum BytePropertyValue {
    Byte(u8),
    String(String),
}

#[derive(Clone, Debug, PartialEq)]
pub enum ArrayValue {
    /// `ArrayProperty` of `ByteProperty`: a raw byte blob.
    Bytes(Vec<u8>),
    /// `ArrayProperty` of `StructProperty`.
    Struct {
        prop_name: String,
        prop_type: String,
        type_name: String,
        id: PalUuid,
        values: Vec<StructValue>,
    },
    Ints(Vec<i32>),
    UInt32s(Vec<u32>),
    Int64s(Vec<i64>),
    Floats(Vec<f32>),
    /// Str/Name/Enum element arrays share the string representation.
    Strings(Vec<String>),
    Bools(Vec<bool>),
}

/// Scalar or struct value inside map entries and sets.
#[derive(Clone, Debug, PartialEq)]
pub enum MapPropValue {
    Bool(bool),
    Int(i32),
    UInt32(u32),
    Int64(i64),
    Str(String),
    Name(String),
    Enum(String),
    Struct(Box<StructValue>),
}

#[derive(Clone, Debug, PartialEq)]
pub struct MapValue {
    pub key_type: String,
    pub value_type: String,
    /// Resolved struct layouts for typed keys/values (from type hints).
    pub key_struct_type: Option<String>,
    pub value_struct_type: Option<String>,
    pub id: Option<PalUuid>,
    pub entries: Vec<(MapPropValue, MapPropValue)>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SetValue {
    pub set_type: String,
    pub struct_type: Option<String>,
    pub id: Option<PalUuid>,
    pub values: SetValues,
}

#[derive(Clone, Debug, PartialEq)]
pub enum SetValues {
    Struct(Vec<StructValue>),
    Properties(Vec<Vec<PropertyEntry>>),
}

#[derive(Clone, Debug, PartialEq)]
pub enum PropertyValue {
    Struct {
        struct_type: String,
        struct_id: PalUuid,
        id: Option<PalUuid>,
        value: Box<StructValue>,
    },
    Int {
        id: Option<PalUuid>,
        value: i32,
    },
    UInt16 {
        id: Option<PalUuid>,
        value: u16,
    },
    UInt32 {
        id: Option<PalUuid>,
        value: u32,
    },
    UInt64 {
        id: Option<PalUuid>,
        value: u64,
    },
    Int64 {
        id: Option<PalUuid>,
        value: i64,
    },
    /// FixedPoint64 values are stored as raw scaled i32.
    FixedPoint64 {
        id: Option<PalUuid>,
        value: i32,
    },
    Float {
        id: Option<PalUuid>,
        value: f32,
    },
    Str {
        id: Option<PalUuid>,
        value: String,
    },
    Name {
        id: Option<PalUuid>,
        value: String,
    },
    Enum {
        id: Option<PalUuid>,
        enum_type: String,
        value: String,
    },
    Bool {
        id: Option<PalUuid>,
        value: bool,
    },
    Byte {
        id: Option<PalUuid>,
        enum_type: String,
        value: BytePropertyValue,
    },
    Array {
        id: Option<PalUuid>,
        array_type: String,
        value: ArrayValue,
    },
    Map(Box<MapValue>),
    Set(Box<SetValue>),
    /// Opaque bytes for skipped heavy properties (foliage, spawners) — preserved verbatim.
    /// Used by the GUI summary profile to avoid parsing ~MB of unused data while
    /// keeping byte-perfect roundtrip. CLI full-decode profile does not use this.
    Opaque {
        raw: Vec<u8>,
    },
}
