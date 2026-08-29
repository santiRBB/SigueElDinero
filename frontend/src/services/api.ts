export interface PaisResumen {
  iso_alpha3: string
  nombre: string
  importe_total_eur: number
  n_intervenciones: number
}

export interface GrupoImporte {
  codigo_grupo: string | null
  nombre: string | null
  importe_eur: number
  n_intervenciones: number
}

export interface AnioImporte {
  anio: number
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
  url_fuente: string | null
}

export interface ProyectoBusqueda extends Proyecto {
  pais_iso3: string
  pais_nombre: string
  codigo_grupo: string | null
  grupo_nombre: string | null
}

export interface PaisDetalle {
  pais: { iso_alpha3: string; nombre: string; region: string | null }
  categorias: GrupoImporte[]
  proyectos: Proyecto[]
}

export interface Grupo {
  codigo_grupo: string
  nombre: string
}

export interface ResultadoBusqueda {
  total: number
  pagina: number
  por_pagina: number
  resultados: ProyectoBusqueda[]
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

export function getResumenPaises(anio?: number, grupo?: string): Promise<PaisResumen[]> {
  return getJSON<PaisResumen[]>('/api/paises/resumen', { anio, grupo })
}

export function getDetallePais(isoAlpha3: string, anio?: number): Promise<PaisDetalle> {
  return getJSON<PaisDetalle>(`/api/paises/${isoAlpha3}/detalle`, { anio })
}

export function getPaisPorAnio(isoAlpha3: string, grupo?: string): Promise<AnioImporte[]> {
  return getJSON<AnioImporte[]>(`/api/paises/${isoAlpha3}/por-anio`, { grupo })
}

export function getAnios(): Promise<number[]> {
  return getJSON<number[]>('/api/filtros/anios')
}

export function getSectores(): Promise<Grupo[]> {
  return getJSON<Grupo[]>('/api/filtros/sectores')
}

export function getResumenPorAnio(grupo?: string): Promise<AnioImporte[]> {
  return getJSON<AnioImporte[]>('/api/resumen/por-anio', { grupo })
}

export function getResumenPorGrupo(anio?: number): Promise<GrupoImporte[]> {
  return getJSON<GrupoImporte[]>('/api/resumen/por-grupo', { anio })
}

export function buscarProyectos(params: {
  q?: string
  anio?: number
  grupo?: string
  pais?: string
  pagina?: number
  por_pagina?: number
}): Promise<ResultadoBusqueda> {
  return getJSON<ResultadoBusqueda>('/api/proyectos/buscar', params)
}
