const TABLE1 = "GN5BH8QJSAC0MFR6P4VET1O7K9U2LD3I";
const TABLE2 = "0123456789abcdefghijklmnopqrstuv";
const V2_KEYS = ["OYD78+MIP3", "N+Q09V7LI5"];
const TYPE_LEN = 3;
const VAR_LEN = 4;
const CODE_LEN = 33;
const PREFIX = "n123git.sayshi/";

function requireCryptoJs() {
  if (!globalThis.CryptoJS) {
    throw new Error("CryptoJS is not loaded.");
  }
  return globalThis.CryptoJS;
}

function wordArrayToBytes(wordArray) {
  const out = new Uint8Array(wordArray.sigBytes);
  for (let i = 0; i < wordArray.sigBytes; i += 1) {
    out[i] = (wordArray.words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff;
  }
  return out;
}

function encodeDigest(bytes) {
  const nibbles = Array.from(bytes)
    .flatMap((byte) => [byte >>> 4, byte & 0x0f]);

  const out = [];
  let bitPos = 0;
  let nibblePos = 0;

  while (nibblePos < nibbles.length) {
    let word = (nibbles[nibblePos] << 28) >>> 0;
    if (nibblePos + 1 < nibbles.length) {
      word = (word | (nibbles[nibblePos + 1] << 24)) >>> 0;
    }

    let value = (word >>> (32 - 5 - bitPos)) & 0x1f;
    if (nibblePos + 1 >= nibbles.length) value >>>= 2;
    out.push(TABLE1[value]);

    bitPos += 5;
    while (bitPos >= 4) {
      bitPos -= 4;
      nibblePos += 1;
    }
  }

  return out.join("");
}

export function base36(value, width = 0) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) throw new Error("Invalid base36 value.");
  return Math.trunc(n).toString(36).toUpperCase().padStart(width, "0");
}

export function fromBase36(value) {
  if (!/^[0-9A-Z]+$/i.test(value)) throw new Error("Invalid base36 text.");
  return Number.parseInt(value, 36);
}

export function normalizeType(type) {
  const value = String(type ?? "").trim().toUpperCase();
  if (!/^[0-9A-Z]{1,3}$/.test(value)) {
    throw new Error("Type must be 1-3 base36 characters.");
  }
  return value.padStart(TYPE_LEN, "0");
}

export function normalizeVariation(variation) {
  const value = String(variation ?? "").trim().toUpperCase();
  if (!/^[0-9A-Z]{1,4}$/.test(value)) {
    throw new Error("Variation must be 1-4 base36 characters.");
  }
  return value.padStart(VAR_LEN, "0");
}

export function variationFromIndex(index) {
  const max = 36 ** VAR_LEN;
  const value = Number(index);
  if (!Number.isInteger(value) || value < 0 || value >= max) {
    throw new Error(`Variation index must be between 0 and ${max - 1}.`);
  }
  return base36(value, VAR_LEN);
}

export function randomVariation() {
  const max = 36 ** VAR_LEN;
  if (globalThis.crypto?.getRandomValues) {
    const buf = new Uint32Array(1);
    globalThis.crypto.getRandomValues(buf);
    return variationFromIndex(buf[0] % max);
  }
  return variationFromIndex(Math.floor(Math.random() * max));
}

export function checksumForPattern(pattern) {
  const CryptoJS = requireCryptoJs();
  const normalized = String(pattern ?? "").trim().toUpperCase();
  if (!/^[0-9A-Z]{7}$/.test(normalized)) {
    throw new Error("V2 checksum input must be exactly 7 base36 characters.");
  }

  let message = CryptoJS.enc.Latin1.parse(normalized);
  let digest = null;

  for (const key of V2_KEYS) {
    digest = CryptoJS.HmacMD5(message, CryptoJS.enc.Latin1.parse(key));
    message = CryptoJS.enc.Latin1.parse(
      digest.toString(CryptoJS.enc.Hex).toLowerCase()
    );
  }

  return encodeDigest(wordArrayToBytes(digest));
}

export function makeCode(type, variation) {
  const pattern = normalizeType(type) + normalizeVariation(variation);
  return pattern + checksumForPattern(pattern);
}

export function validateCode(code) {
  const normalized = String(code ?? "").trim().replace(/^\/+/, "").toUpperCase();
  if (!/^[0-9A-Z]{33}$/.test(normalized)) {
    return { valid: false, reason: "Code must be 33 alphanumeric characters." };
  }

  const pattern = normalized.slice(0, TYPE_LEN + VAR_LEN);
  const expected = checksumForPattern(pattern);
  const actual = normalized.slice(TYPE_LEN + VAR_LEN);

  return {
    valid: expected === actual,
    code: normalized,
    type: normalized.slice(0, TYPE_LEN),
    variation: normalized.slice(TYPE_LEN, TYPE_LEN + VAR_LEN),
    checksum: actual,
    expectedChecksum: expected,
  };
}

export function makePayload(code, prefix = PREFIX) {
  const normalized = String(code ?? "").trim().replace(/^\/+/, "");
  return `${prefix}${normalized}`;
}

export function extractCode(input) {
  const raw = String(input ?? "").trim();
  if (!raw) return null;

  const direct = raw.match(/([0-9A-Z]{33})$/i);
  if (direct) return direct[1].toUpperCase();

  const afterSlash = raw.match(/\/([0-9A-Z]{33})(?:[?#].*)?$/i);
  if (afterSlash) return afterSlash[1].toUpperCase();

  const embedded = raw.match(/([0-9A-Z]{33})/i);
  return embedded ? embedded[1].toUpperCase() : null;
}

export function parsePayload(input) {
  const code = extractCode(input);
  if (!code) {
    return { valid: false, reason: "No 33-character V2 code found." };
  }
  return validateCode(code);
}

export const V2 = Object.freeze({
  typeLength: TYPE_LEN,
  variationLength: VAR_LEN,
  codeLength: CODE_LEN,
  defaultPrefix: PREFIX,
  maxVariation: 36 ** VAR_LEN - 1,
});
