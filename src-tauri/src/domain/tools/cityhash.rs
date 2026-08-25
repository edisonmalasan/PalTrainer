//! CityHash64 implementation in pure Rust matching Google CityHash v1.1.1
//! and the reference Python implementation in `palsav._cityhash`.

const K0: u64 = 0xc3a5c85c97cb3127;
const K1: u64 = 0xb492b66fbe98f273;
const K2: u64 = 0x9ae16a3b2f90404f;
const KMUL: u64 = 0x9ddfea08eb382d69;

#[inline]
fn fetch64(p: &[u8]) -> u64 {
    u64::from_le_bytes(p[..8].try_into().unwrap())
}

#[inline]
fn fetch32(p: &[u8]) -> u32 {
    u32::from_le_bytes(p[..4].try_into().unwrap())
}

#[inline]
fn rotate(val: u64, shift: usize) -> u64 {
    val.rotate_right(shift as u32)
}

#[inline]
fn shift_mix(val: u64) -> u64 {
    val ^ (val >> 47)
}

#[inline]
fn hash128to64(x_lo: u64, x_hi: u64) -> u64 {
    let mut a = (x_lo ^ x_hi).wrapping_mul(KMUL);
    a ^= a >> 47;
    let mut b = (x_hi ^ a).wrapping_mul(KMUL);
    b ^= b >> 47;
    b.wrapping_mul(KMUL)
}

#[inline]
fn hash_len16(u: u64, v: u64) -> u64 {
    hash128to64(u, v)
}

#[inline]
fn hash_len16_mul(u: u64, v: u64, mul: u64) -> u64 {
    let mut a = (u ^ v).wrapping_mul(mul);
    a ^= a >> 47;
    let mut b = (v ^ a).wrapping_mul(mul);
    b ^= b >> 47;
    b.wrapping_mul(mul)
}

fn hash_len0to16(s: &[u8], len: usize) -> u64 {
    if len >= 8 {
        let mul = K2.wrapping_add((len as u64).wrapping_mul(2));
        let a = fetch64(s).wrapping_add(K2);
        let b = fetch64(&s[len - 8..]);
        let c = rotate(b, 37).wrapping_mul(mul).wrapping_add(a);
        let d = rotate(a, 25).wrapping_add(b).wrapping_mul(mul);
        return hash_len16_mul(c, d, mul);
    }
    if len >= 4 {
        let mul = K2.wrapping_add((len as u64).wrapping_mul(2));
        let a = fetch32(s) as u64;
        return hash_len16_mul(
            (len as u64).wrapping_add(a << 3),
            fetch32(&s[len - 4..]) as u64,
            mul,
        );
    }
    if len > 0 {
        let a = s[0] as u64;
        let b = s[len >> 1] as u64;
        let c = s[len - 1] as u64;
        let y = (a.wrapping_add(b << 8)) as u32 as u64;
        let z = (len as u64).wrapping_add(c << 2);
        return shift_mix(y.wrapping_mul(K2) ^ z.wrapping_mul(K0)).wrapping_mul(K2);
    }
    K2
}

fn hash_len17to32(s: &[u8], len: usize) -> u64 {
    let mul = K2.wrapping_add((len as u64).wrapping_mul(2));
    let a = fetch64(s).wrapping_mul(K1);
    let b = fetch64(&s[8..]);
    let c = fetch64(&s[len - 8..]).wrapping_mul(mul);
    let d = fetch64(&s[len - 16..]).wrapping_mul(K2);
    hash_len16_mul(
        rotate(a.wrapping_add(b), 43)
            .wrapping_add(rotate(c, 30))
            .wrapping_add(d),
        a.wrapping_add(rotate(b.wrapping_add(K2), 18))
            .wrapping_add(c),
        mul,
    )
}

fn weak_hash_len32_with_seeds_6(
    w: u64,
    x: u64,
    y: u64,
    z: u64,
    mut a: u64,
    mut b: u64,
) -> (u64, u64) {
    a = a.wrapping_add(w);
    b = rotate(b.wrapping_add(a).wrapping_add(z), 21);
    let c = a;
    a = a.wrapping_add(x);
    a = a.wrapping_add(y);
    b = b.wrapping_add(rotate(a, 44));
    (a.wrapping_add(z), b.wrapping_add(c))
}

fn weak_hash_len32_with_seeds(s: &[u8], a: u64, b: u64) -> (u64, u64) {
    weak_hash_len32_with_seeds_6(
        fetch64(&s[0..8]),
        fetch64(&s[8..16]),
        fetch64(&s[16..24]),
        fetch64(&s[24..32]),
        a,
        b,
    )
}

fn byteswap64(x: u64) -> u64 {
    x.swap_bytes()
}

fn hash_len33to64(s: &[u8], len: usize) -> u64 {
    let mul = K2.wrapping_add((len as u64).wrapping_mul(2));
    let a = fetch64(s).wrapping_mul(K2);
    let b = fetch64(&s[8..]);
    let c = fetch64(&s[len - 24..]);
    let d = fetch64(&s[len - 32..]);
    let e = fetch64(&s[16..24]).wrapping_mul(K2);
    let f = fetch64(&s[24..32]).wrapping_mul(9);
    let g = fetch64(&s[len - 8..]);
    let h = fetch64(&s[len - 16..]).wrapping_mul(mul);
    let u =
        rotate(a.wrapping_add(g), 43).wrapping_add(rotate(b, 30).wrapping_add(c).wrapping_mul(9));
    let v = ((a.wrapping_add(g)) ^ d).wrapping_add(f).wrapping_add(1);
    let w = byteswap64(u.wrapping_add(v).wrapping_mul(mul)).wrapping_add(h);
    let x = rotate(e.wrapping_add(f), 42).wrapping_add(c);
    let y = byteswap64(v.wrapping_add(w).wrapping_mul(mul))
        .wrapping_add(g)
        .wrapping_mul(mul);
    let z = e.wrapping_add(f).wrapping_add(c);
    let a2 = byteswap64(x.wrapping_add(z).wrapping_mul(mul).wrapping_add(y)).wrapping_add(b);
    let b2 = shift_mix(
        z.wrapping_add(a2)
            .wrapping_mul(mul)
            .wrapping_add(d)
            .wrapping_add(h),
    )
    .wrapping_mul(mul);
    b2.wrapping_add(x)
}

/// Computes 64-bit CityHash over the given byte slice.
pub fn cityhash64(data: &[u8]) -> u64 {
    let len = data.len();
    if len <= 32 {
        if len <= 16 {
            return hash_len0to16(data, len);
        }
        return hash_len17to32(data, len);
    }
    if len <= 64 {
        return hash_len33to64(data, len);
    }

    let mut x = fetch64(&data[len - 40..len - 32]);
    let mut y = fetch64(&data[len - 16..len - 8]).wrapping_add(fetch64(&data[len - 56..len - 48]));
    let mut z = hash_len16(
        fetch64(&data[len - 48..len - 40]).wrapping_add(len as u64),
        fetch64(&data[len - 24..len - 16]),
    );
    let mut v = weak_hash_len32_with_seeds(&data[len - 64..len - 32], len as u64, z);
    let mut w = weak_hash_len32_with_seeds(&data[len - 32..], y.wrapping_add(K1), x);
    x = x.wrapping_mul(K1).wrapping_add(fetch64(data));

    let mut remaining = (len - 1) & !63;
    let mut pos = 0;
    while remaining != 0 {
        x = rotate(
            x.wrapping_add(y)
                .wrapping_add(v.0)
                .wrapping_add(fetch64(&data[pos + 8..pos + 16])),
            37,
        )
        .wrapping_mul(K1);
        y = rotate(
            y.wrapping_add(v.1)
                .wrapping_add(fetch64(&data[pos + 48..pos + 56])),
            42,
        )
        .wrapping_mul(K1);
        x ^= w.1;
        y = y
            .wrapping_add(v.0)
            .wrapping_add(fetch64(&data[pos + 40..pos + 48]));
        z = rotate(z.wrapping_add(w.0), 33).wrapping_mul(K1);
        v = weak_hash_len32_with_seeds(
            &data[pos..pos + 32],
            v.1.wrapping_mul(K1),
            x.wrapping_add(w.0),
        );
        w = weak_hash_len32_with_seeds(
            &data[pos + 32..pos + 64],
            z.wrapping_add(w.1),
            y.wrapping_add(fetch64(&data[pos + 16..pos + 24])),
        );
        std::mem::swap(&mut z, &mut x);
        pos += 64;
        remaining -= 64;
    }

    hash_len16(
        hash_len16(v.0, w.0)
            .wrapping_add(shift_mix(y).wrapping_mul(K1))
            .wrapping_add(z),
        hash_len16(v.1, w.1).wrapping_add(x),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cityhash_empty() {
        assert_eq!(cityhash64(b""), K2);
    }

    #[test]
    fn test_cityhash_short() {
        let h = cityhash64(b"hello");
        assert_ne!(h, 0);
    }
}
