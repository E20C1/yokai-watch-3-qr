import { QR2_GZIP_BASE64 } from "../data/qr2-jp40.js";

function base64Bytes(value) {
  const binary = atob(value);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i);
  return out;
}

export async function loadQr2Dataset() {
  const bytes = base64Bytes(QR2_GZIP_BASE64);

  if ("DecompressionStream" in globalThis) {
    const stream = new Blob([bytes])
      .stream()
      .pipeThrough(new DecompressionStream("gzip"));
    return new Response(stream).json();
  }

  if (globalThis.pako) {
    const decoded = globalThis.pako.ungzip(bytes);
    return JSON.parse(new TextDecoder().decode(decoded));
  }

  throw new Error("This browser cannot decompress the embedded dataset.");
}
