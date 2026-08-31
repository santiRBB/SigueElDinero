export const RAMP = ['#D7E2EB', '#A9C1D5', '#7699B8', '#43709A', '#1D4E7B', '#0B3B5C']

// Grey used across the maps and the legend for regions/countries with no
// data (as opposed to a real value of 0), kept lowercase to match the
// original literal in MapLegend.vue.
export const COLOR_SIN_DATOS = '#e6e1d7'

// visualMap has no native quantile scale, so the 5 cut points are computed
// by hand from the values actually present (same criterion as the design
// reference's d3.scaleThreshold over quantiles). With fewer than 6 values
// there aren't enough data points for meaningful quantiles, so we fall back
// to evenly-spaced cuts between the min and max instead.
export function calcularCortes(valores: number[]): number[] {
  const ordenados = [...valores].sort((a, b) => a - b)
  if (ordenados.length === 0) return [1, 2, 3, 4, 5]
  if (ordenados.length < 6) {
    const min = ordenados[0]
    const max = ordenados[ordenados.length - 1]
    const paso = (max - min) / 6 || 1
    return [1, 2, 3, 4, 5].map((i) => min + paso * i)
  }
  const cuantil = (p: number): number => {
    const idx = p * (ordenados.length - 1)
    const lo = Math.floor(idx)
    const hi = Math.ceil(idx)
    if (lo === hi) return ordenados[lo]
    return ordenados[lo] + (ordenados[hi] - ordenados[lo]) * (idx - lo)
  }
  return [0.16, 0.34, 0.52, 0.7, 0.86].map(cuantil)
}

// Shared piecewise-legend builder used by both WorldMap.vue and SpainMap.vue:
// takes the raw importe_total_eur values for every entry in a resumen array,
// filters out non-positive ones (0 or missing means "no data", not the
// lightest bucket), computes the cut points, and pairs them up against RAMP.
export function calcularPieces(valores: number[]): { min: number; max: number; color: string }[] {
  const positivos = valores.filter((v) => v > 0)
  const cortes = calcularCortes(positivos)
  const limites = [0, ...cortes, Infinity]
  return RAMP.map((color, i) => ({ min: limites[i], max: limites[i + 1], color }))
}
