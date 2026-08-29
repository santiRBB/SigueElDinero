import { describe, expect, it } from 'vitest'
import { formatEUR, formatEURCompacto, formatFecha, formatPorcentaje } from './formato'

describe('formatEUR', () => {
  it('formats as euros with no decimals', () => {
    expect(formatEUR(1234)).toContain('1.234')
    expect(formatEUR(1234)).toContain('€')
  })
})

describe('formatEURCompacto', () => {
  it('uses MM for billions', () => {
    expect(formatEURCompacto(2_500_000_000)).toContain('MM')
  })
  it('uses M for millions', () => {
    expect(formatEURCompacto(3_200_000)).toContain('M')
    expect(formatEURCompacto(3_200_000)).not.toContain('MM')
  })
  it('uses k for thousands', () => {
    expect(formatEURCompacto(4_500)).toContain('k')
  })
  it('spells out small amounts', () => {
    expect(formatEURCompacto(500)).toContain('500')
    expect(formatEURCompacto(500)).not.toContain('k')
  })
})

describe('formatPorcentaje', () => {
  it('formats with one decimal and a percent sign', () => {
    expect(formatPorcentaje(42.567)).toBe('42,6 %')
  })
})

describe('formatFecha', () => {
  it('formats an ISO date as "mes. año"', () => {
    expect(formatFecha('2024-10-15')).toBe('oct. 2024')
  })
  it('returns "en curso" for a null date', () => {
    expect(formatFecha(null)).toBe('en curso')
  })
})
