// The one Node function the test uses (so the build needs no @types/node).
declare module "node:fs" {
  export function readFileSync(path: string, encoding: "utf-8"): string;
}
