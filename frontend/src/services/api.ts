export interface PaisResumen {
  iso_alpha3: string
  nombre: string
  importe_total_eur: number
  n_intervenciones: number
}

export interface Categoria {
  codigo_crs: string | null
  nombre: string | null
  importe_eur: number
  n_intervenciones: number
}

export interface Proyecto {
  aid: string
  titulo: string | null
  organismo_ejecutor: string | null
  importe_pais_eur: number
  porcentaje_pais: number | null
  porcentaje_fuente: 'declared' | 'assumed_equal_split' | null
  start_date: string | null
  end_date: string | null
}

export interface PaisDetalle {
  pais: { iso_alpha3: string; nombre: string; region: string | null }
  categorias: Categoria[]
  proyectos: Proyecto[]
}

export interface Sector {
  codigo_crs: string
  nombre: string | null
}

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

async function getJSON<T>(path: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value))
    }
  }

  const response = await fetch(url.toString())
  if (!response.ok) {
    throw new Error(`Error ${response.status} al llamar a ${path}`)
  }
  return response.json() as Promise<T>
}

export function getResumenPaises(anio?: number, sector?: string): Promise<PaisResumen[]> {
  return getJSON<PaisResumen[]>('/api/paises/resumen', { anio, sector })
}

export function getDetallePais(isoAlpha3: string, anio?: number): Promise<PaisDetalle> {
  return getJSON<PaisDetalle>(`/api/paises/${isoAlpha3}/detalle`, { anio })
}

export function getAnios(): Promise<number[]> {
  return getJSON<number[]>('/api/filtros/anios')
}

export function getSectores(): Promise<Sector[]> {
  return getJSON<Sector[]>('/api/filtros/sectores')
}
