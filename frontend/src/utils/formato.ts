const nfEntero = new Intl.NumberFormat('es-ES', { useGrouping: true })
const nfUnDecimal = new Intl.NumberFormat('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1, useGrouping: true })

export function formatEUR(valor: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0, useGrouping: true }).format(valor)
}

export function formatEURCompacto(valor: number): string {
  if (valor >= 1e9) return nfUnDecimal.format(valor / 1e9) + ' MM €'
  if (valor >= 1e6) return nfUnDecimal.format(valor / 1e6) + ' M €'
  if (valor >= 1e3) return Math.round(valor / 1e3) + ' k €'
  return nfEntero.format(valor) + ' €'
}

export function formatPorcentaje(valor: number): string {
  return nfUnDecimal.format(valor) + ' %'
}

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

export function formatFecha(iso: string | null): string {
  if (!iso) return 'en curso'
  const [anio, mes] = iso.split('-')
  return `${MESES[Number(mes) - 1]}. ${anio}`
}
