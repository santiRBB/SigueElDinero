import { describe, expect, it } from 'vitest'
import { RAMP, calcularCortes, calcularPieces } from './mapaColores'

describe('calcularCortes', () => {
  it('returns fixed placeholder cuts when there are no values', () => {
    expect(calcularCortes([])).toEqual([1, 2, 3, 4, 5])
  })

  it('returns evenly-spaced cuts when there are fewer than 6 values', () => {
    const result = calcularCortes([10, 20, 30])

    expect(result).toHaveLength(5)
    expect(result[0]).toBeCloseTo(13.333, 2)
    expect(result[1]).toBeCloseTo(16.667, 2)
    expect(result[2]).toBeCloseTo(20)
    expect(result[3]).toBeCloseTo(23.333, 2)
    expect(result[4]).toBeCloseTo(26.667, 2)
  })

  it('returns quantile-based cuts when there are 6 or more values', () => {
    const result = calcularCortes([10, 20, 30, 40, 50, 60])

    expect(result).toHaveLength(5)
    expect(result[0]).toBeCloseTo(18)
    expect(result[1]).toBeCloseTo(27)
    expect(result[2]).toBeCloseTo(36)
    expect(result[3]).toBeCloseTo(45)
    expect(result[4]).toBeCloseTo(53)
  })
})

describe('calcularPieces', () => {
  it('returns one piece per RAMP color, zipped against the computed cuts', () => {
    const valores = [10, 20, 30, 40, 50, 60]
    const cortes = calcularCortes(valores)

    const pieces = calcularPieces(valores)

    expect(pieces).toHaveLength(RAMP.length)
    expect(pieces.map((p) => p.color)).toEqual(RAMP)
    expect(pieces[0].min).toBe(0)
    expect(pieces[0].max).toBeCloseTo(cortes[0])
    expect(pieces[pieces.length - 1].min).toBeCloseTo(cortes[cortes.length - 1])
    expect(pieces[pieces.length - 1].max).toBe(Infinity)
  })

  it('ignores non-positive values, treating them as absent rather than the lightest bucket', () => {
    const withZeros = calcularPieces([0, 0, 10, 20, 30, 40, 50, 60])
    const withoutZeros = calcularPieces([10, 20, 30, 40, 50, 60])

    expect(withZeros).toEqual(withoutZeros)
  })
})
