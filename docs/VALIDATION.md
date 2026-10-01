# Validation

## Browser self-test

At startup the browser generates the following code:

```text
pattern: Q1B0000
expected:
Q1B00008CLTN07O0A2VJ3EU5L3LETAB3G
```

If the generated result differs, the Research tab displays `FAIL`.

## Dataset validation

Run:

```bash
python tools/validate_dataset.py
```

The validator checks:

- entry count
- Type/base36 consistency
- valid Type ranges
- 32-bit hex field formatting
- expected special-entry counts
- overlap diagnostics

## Hardware validation

The checksum algorithm and table lookup can be validated offline, but actual acceptance by a specific retail build is ultimately an implementation detail of that game build.

For JP Sukiyaki Ver.4.0, the recommended smoke test is a known single-item QR entry, followed by comparison with the expected inventory change.

Flag-bearing entries should not be the first hardware test.
