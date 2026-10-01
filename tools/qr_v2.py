#!/usr/bin/env python3
"""Minimal Level-5 V2 QR code string generator used by YW3 QR Lab."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import secrets
import string

TABLE1 = "GN5BH8QJSAC0MFR6P4VET1O7K9U2LD3I"
TABLE2 = "0123456789abcdefghijklmnopqrstuv"
KEYS = (b"OYD78+MIP3", b"N+Q09V7LI5")
BASE36 = string.digits + string.ascii_uppercase


def encode_digest(data: bytes) -> str:
    nibbles: list[int] = []
    for byte in data:
        nibbles.extend((byte >> 4, byte & 0x0F))

    out: list[str] = []
    bit_pos = 0
    pos = 0
    while pos < len(nibbles):
        word = (nibbles[pos] << 28) & 0xFFFFFFFF
        if pos + 1 < len(nibbles):
            word |= (nibbles[pos + 1] << 24) & 0xFFFFFFFF

        value = (word >> (32 - 5 - bit_pos)) & 0x1F
        if pos + 1 >= len(nibbles):
            value >>= 2
        out.append(TABLE1[value])

        bit_pos += 5
        while bit_pos >= 4:
            bit_pos -= 4
            pos += 1
    return "".join(out)


def checksum(pattern: str) -> str:
    pattern = pattern.upper()
    if len(pattern) != 7 or any(ch not in BASE36 for ch in pattern):
        raise ValueError("pattern must be 7 base36 characters")

    message = pattern.encode("ascii")
    digest = b""
    for key in KEYS:
        digest = hmac.new(key, message, hashlib.md5).digest()
        message = digest.hex().encode("latin1")
    return encode_digest(digest)


def make_code(type_: str, variation: str) -> str:
    type_ = type_.upper().zfill(3)
    variation = variation.upper().zfill(4)
    pattern = type_ + variation
    return pattern + checksum(pattern)


def random_variation() -> str:
    value = secrets.randbelow(36**4)
    chars: list[str] = []
    for _ in range(4):
        value, rem = divmod(value, 36)
        chars.append(BASE36[rem])
    return "".join(reversed(chars))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="3-char base36 Type")
    parser.add_argument("--variation", help="4-char base36 Variation")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--payload", action="store_true", help="print QRTool-compatible payload")
    args = parser.parse_args()

    for index in range(max(1, args.count)):
        variation = args.variation or random_variation()
        if args.variation and args.count > 1:
            start = int(args.variation, 36)
            variation = numpy_free_base36((start + index) % (36**4), 4)
        code = make_code(args.type, variation)
        print(("n123git.sayshi/" if args.payload else "") + code)


def numpy_free_base36(value: int, width: int) -> str:
    out = ""
    while value:
        value, rem = divmod(value, 36)
        out = BASE36[rem] + out
    return (out or "0").zfill(width)


if __name__ == "__main__":
    main()
