declare module 'topojson-client' {
  export function feature(topology: unknown, object: unknown): { features: Array<{ id?: string | number; properties: Record<string, unknown> }> }
}
