import { describe, expect, it } from 'vitest'
import { calcularCortes } from './mapaColores'

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
