// Copia sites.json y los JSON precalculados del backend a src/mocks/data/.
// Uso: npm run sync-mocks   (ejecutar de nuevo cuando lleguen datos reales)
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "..", "backend", "data");
const dst = join(root, "src", "mocks", "data");

if (!existsSync(join(src, "sites.json"))) {
  console.error(`No encuentro ${src}/sites.json`);
  process.exit(1);
}
rmSync(dst, { recursive: true, force: true });
mkdirSync(dst, { recursive: true });
cpSync(join(src, "sites.json"), join(dst, "sites.json"));
for (const id of readdirSync(join(src, "precomputed"))) {
  const dir = join(src, "precomputed", id);
  if (!existsSync(join(dir, "timeseries.json"))) continue;
  mkdirSync(join(dst, id), { recursive: true });
  for (const k of ["horizon", "terrain", "timeseries"]) {
    if (existsSync(join(dir, `${k}.json`))) cpSync(join(dir, `${k}.json`), join(dst, id, `${k}.json`));
  }
  console.log(`mock: ${id}`);
}
