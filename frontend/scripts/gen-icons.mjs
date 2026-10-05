// Generates solid indigo PNG icons with a white rounded "camera/photo" shape. No deps.
import { deflateSync } from "node:zlib";
import { writeFileSync } from "node:fs";

const crcT = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = (b) => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };

function png(size) {
  const raw = Buffer.alloc((size * 3 + 1) * size);
  const s = size / 512;
  for (let y = 0; y < size; y++) {
    raw[y * (size * 3 + 1)] = 0;
    for (let x = 0; x < size; x++) {
      const px = x / s, py = y / s;
      let c = [79, 70, 229];
      const body = px > 136 && px < 376 && py > 190 && py < 352;
      const top = px > 210 && px < 302 && py > 160 && py <= 190;
      const lens = (px - 256) ** 2 + (py - 271) ** 2 < 52 ** 2;
      if (lens) c = [79, 70, 229]; else if (body || top) c = [255, 255, 255];
      const o = y * (size * 3 + 1) + 1 + x * 3; raw[o] = c[0]; raw[o + 1] = c[1]; raw[o + 2] = c[2];
    }
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(size, 0); ihdr.writeUInt32BE(size, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}
for (const n of [192, 512]) writeFileSync(`public/icon-${n}.png`, png(n));
