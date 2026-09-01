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
  sector_crs_code: string | null
  sector_crs_nombre: string | null
  importe_pais_eur: number
  porcentaje_pais: number | null
  porcentaje_fuente: 'declared' | 'assumed_equal_split' | null
  start_date: string | null
  end_date: string | null
  url_fuente: string | null
  url_bdns: string | null
  bdns_tipo_convocatoria: string | null
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

export interface CcaaResumen {
  codigo_ine: string
  nombre: string
  importe_total_eur: number
  n_concesiones: number
}

export interface CcaaOrganismo {
  organismo: string
  importe_total_eur: number
  n_concesiones: number
}

export interface CcaaDetalle {
  ccaa: { codigo_ine: string; nombre: string }
  importe_total_eur: number
  n_concesiones: number
  organismos: CcaaOrganismo[]
}

export interface CcaaAnio {
  anio: number
  importe_eur: number
  n_concesiones: number
}

export interface Grupo {
  codigo_grupo: string
  nombre: string
}

export interface AecidBdnsPais {
  iso_alpha3: string
  importe_eur: number
  n_concesiones: number
}

export interface AecidBdnsResumen {
  por_pais: AecidBdnsPais[]
  sin_pais: { importe_eur: number; n_concesiones: number }
}

export type Orden = 'importe_desc' | 'importe_asc' | 'fecha_desc' | 'fecha_asc'

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
    const error = new Error(`Error ${response.status} al llamar a ${path}`) as Error & { status: number }
    error.status = response.status
    throw error
  }
  return response.json() as Promise<T>
}

export function getResumenPaises(anio?: number, grupo?: string): Promise<PaisResumen[]> {
  return getJSON<PaisResumen[]>('/api/paises/resumen', { anio, grupo })
}

export function getDetallePais(isoAlpha3: string, anio?: number, grupo?: string): Promise<PaisDetalle> {
  return getJSON<PaisDetalle>(`/api/paises/${isoAlpha3}/detalle`, { anio, grupo })
}

export function getPaisPorAnio(isoAlpha3: string, grupo?: string): Promise<AnioImporte[]> {
  return getJSON<AnioImporte[]>(`/api/paises/${isoAlpha3}/por-anio`, { grupo })
}

export function getResumenCcaa(anio?: number): Promise<CcaaResumen[]> {
  return getJSON<CcaaResumen[]>('/api/ccaa/resumen', { anio })
}

export function getDetalleCcaa(codigoIne: string, anio?: number): Promise<CcaaDetalle> {
  return getJSON<CcaaDetalle>(`/api/ccaa/${codigoIne}/detalle`, { anio })
}

export function getResumenAecidBdns(): Promise<AecidBdnsResumen> {
  return getJSON<AecidBdnsResumen>('/api/aecid-bdns/resumen')
}

export function getCcaaPorAnio(codigoIne: string): Promise<CcaaAnio[]> {
  return getJSON<CcaaAnio[]>(`/api/ccaa/${codigoIne}/por-anio`)
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
  orden?: Orden
}): Promise<ResultadoBusqueda> {
  return getJSON<ResultadoBusqueda>('/api/proyectos/buscar', params)
}
