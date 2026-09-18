export const ORIGEN = 'https://sigueeldinero.es'
export const NOMBRE_SITIO = 'Sigue el dinero'

export interface MetaRuta {
  titulo: string
  descripcion: string
  indexable: boolean
  anuncios: boolean
}

export const META_RUTAS: Record<string, MetaRuta> = {
  '/': {
    titulo: 'Sigue el dinero',
    descripcion:
      'Cuánto dinero destina España a la cooperación internacional, a qué países y en qué sectores. Datos oficiales de AECID publicados en el estándar IATI.',
    indexable: true,
    anuncios: true,
  },
  '/mapa': {
    titulo: 'El reparto, país a país',
    descripcion:
      'Mapa y tabla de la cooperación española por país receptor: importe comprometido, número de intervenciones y evolución por año.',
    indexable: true,
    anuncios: true,
  },
  '/proyectos': {
    titulo: 'Buscador de proyectos',
    descripcion:
      'Busca entre los proyectos de cooperación de AECID por país, entidad ejecutora, sector o palabra del título.',
    indexable: true,
    anuncios: true,
  },
  '/analisis': {
    titulo: 'Análisis',
    descripcion:
      'Artículos sobre cómo se publica, se clasifica y se lee el dinero de la cooperación española, y sobre lo que los datos oficiales no cuentan.',
    indexable: true,
    anuncios: true,
  },
  '/analisis/:slug': {
    titulo: 'Análisis',
    descripcion:
      'Artículos sobre cómo se publica, se clasifica y se lee el dinero de la cooperación española.',
    indexable: true,
    anuncios: true,
  },
  '/sobre': {
    titulo: 'Qué contiene esta web y qué no',
    descripcion:
      'Metodología: de dónde salen los datos, qué mide cada cifra, cómo se reparten los importes entre países y qué queda fuera.',
    indexable: true,
    anuncios: true,
  },
  '/paises/:iso3': {
    titulo: 'Ficha de país',
    descripcion: 'Cooperación española en un país: importe, sectores, entidades ejecutoras y proyectos.',
    indexable: false,
    anuncios: false,
  },
  '/ccaa/:codigoIne': {
    titulo: 'Ficha de comunidad autónoma',
    descripcion: 'Concesiones de subvenciones públicas registradas en BDNS por comunidad autónoma.',
    indexable: false,
    anuncios: false,
  },
  '/cookies': {
    titulo: 'Política de cookies',
    descripcion: 'Qué cookies usa este sitio y cómo cambiar tus preferencias.',
    indexable: false,
    anuncios: false,
  },
}

export const RUTAS_INDEXABLES = Object.entries(META_RUTAS)
  .filter(([path, meta]) => meta.indexable && !path.includes(':'))
  .map(([path]) => path)
