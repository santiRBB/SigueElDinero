# SigueElDinero — Plan de diseño del frontend

## 1. Alcance de esta fase (MVP)

- Mapa mundi tipo heatmap: intensidad de color por país según importe total recibido de cooperación española (fuente: `fact_gasto`, datos IATI/AECID ya cargados en Supabase).
- Al clicar un país: panel lateral/modal con desglose por categoría (sector CRS), lista de proyectos individuales, importe total y nº de intervenciones.
- Filtro global por año (rango `start_date`/`end_date`) y por sector.
- Fuera de alcance para esta fase: vista de gasto interno en España (BDNS/IGAE) — se añade como fase 2 con su propio mapa/vista (mapa de CCAA en vez de mundial).

## 2. Stack técnico

Reutilizando tu stack habitual:

| Capa | Elección | Por qué |
|---|---|---|
| Framework | Vue 3 + Vite | Ya lo usas en WerkTax/CopControl |
| Estado | Pinia | Estándar Vue 3, encaja con Vite |
| Mapa | **ECharts** vía `vue-echarts` | Trae choropleth de mundo + leyenda + tooltip + animaciones ya resueltos (`visualMap` + `map` series). Mucho menos esfuerzo que D3 a mano para este caso de uso, y sigue siendo muy personalizable si luego quieres afinar estilos |
| HTTP | `fetch` nativo o `axios` (indistinto) | — |
| Backend | FastAPI (ya lo tienes) | Sirve los endpoints agregados, no exponemos Supabase directo al navegador |
| Hosting | Netlify (frontend) + Render (API) | Mismo patrón que WerkTax |

**Nota sobre ECharts vs D3**: si más adelante quieres control total del dibujo (transiciones custom, mapas no estándar), migrar a D3 + `topojson` es factible sin rehacer el resto de la app, porque el mapa vive en un componente aislado (`WorldMap.vue`).

## 3. Endpoints necesarios en el backend (FastAPI)

No expongas Supabase directamente desde el navegador — mejor pasar por tu API para poder cachear, controlar CORS y agregar sin recalcular en el cliente.

```
GET /api/paises/resumen?anio=2025&sector=72050
  -> [{ iso_alpha3, nombre, importe_total_eur, n_intervenciones }, ...]
  Usado para pintar el heatmap (un valor agregado por país)

GET /api/paises/{iso_alpha3}/detalle?anio=2025
  -> {
       pais: {...},
       categorias: [{ codigo_crs, nombre, importe_eur, n_intervenciones }, ...],
       proyectos: [{ aid, titulo, organismo_ejecutor, importe_pais_eur,
                      porcentaje_pais, porcentaje_fuente, start_date, end_date }, ...]
     }
  Usado para el panel lateral al clicar un país

GET /api/filtros/anios
  -> [2023, 2024, 2025, 2026, ...]   (años disponibles, para el selector)

GET /api/filtros/sectores
  -> [{ codigo_crs, nombre }, ...]   (para el selector de categoría)
```

Todos con agregación `SUM(importe_pais_eur)` y `COUNT(*)` en SQL, no en el frontend.

## 4. Estructura de carpetas propuesta

```
src/
  components/
    WorldMap.vue          -- el mapa ECharts, emite evento @country-click
    CountryPanel.vue       -- panel lateral con desglose al clicar un país
    FilterBar.vue          -- selectores de año y sector
    ProjectCard.vue        -- tarjeta individual de proyecto dentro del panel
    AmountBadge.vue        -- pill "importe estimado" vs "declarado" (ver sección 6)
  stores/
    gastoStore.ts          -- Pinia: paisesResumen, paisSeleccionado, filtros activos
  services/
    api.ts                 -- wrappers fetch a los endpoints de arriba
  views/
    MapaView.vue           -- pantalla principal (mapa + panel + filtros)
  assets/
    world.json             -- topología del mundo para ECharts (registrar con echarts.registerMap)
```

## 5. Flujo de datos (Pinia)

```
gastoStore
  state:
    paisesResumen: []       // cache de GET /paises/resumen
    paisSeleccionado: null  // iso_alpha3 actualmente clicado
    detallePais: null       // cache del detalle del país seleccionado
    filtroAnio: null
    filtroSector: null
  actions:
    cargarResumen()         // llama a la API cuando cambian los filtros
    seleccionarPais(iso3)   // llama a /paises/{iso3}/detalle y abre el panel
```

`WorldMap.vue` solo lee `paisesResumen` y emite `@click` con el iso3; no conoce el detalle. `CountryPanel.vue` solo lee `detallePais`. Esto mantiene cada componente simple y testeable por separado.

## 6. Decisiones de UX importantes (por la naturaleza de los datos)

Estas vienen directamente de lo que descubrimos validando los datos — no son detalles cosméticos, evitan que la web parezca menos rigurosa de lo que es:

- **Distinguir `porcentaje_fuente`**: si es `"assumed_equal_split"`, mostrar un badge tipo "reparto estimado entre países" junto al importe de ese proyecto. Si es `"declared"`, no hace falta ninguna marca especial (es el caso normal).
- **Importes idénticos entre proyectos** (recuerda el caso de los ~985.865€ repetidos en la convocatoria humanitaria de oct-2024): en `ProjectCard.vue`, si detectas mismo importe + misma fecha de transacción en varios proyectos de la lista, mostrar una nota discreta tipo *"Importe estándar de esta convocatoria"* en vez de dejar que parezca casualidad.
- **Escala de color del heatmap**: usar escala logarítmica, no lineal — el gasto de cooperación está muy concentrado (pocos países grandes reciben mucho, la mayoría reciben poco), y con escala lineal el mapa saldría casi monocromo excepto 2-3 países.
- **Países sin datos**: gris neutro, no blanco (para no confundir "sin cooperación" con "sin datos cargados aún").
- **Tooltip del mapa**: nombre país + importe total + nº proyectos, sin abrir el panel completo (el panel se abre solo al clic, el hover es solo vista rápida).

## 7. Roadmap de fases

| Fase | Contenido |
|---|---|
| **1 (esta)** | Mapa mundi + AECID/IATI, filtro año/sector, panel de detalle |
| **2** | Vista "España interior": mapa de CCAA con datos BDNS/IGAE (pendiente de retomar la exploración de BDNS que dejamos aparcada) |
| **3** | Buscador de texto libre sobre `titulo`/`descripcion`, comparativas entre países, export CSV del detalle |
| **4** | Ingesta de más organismos IATI españoles (si aparecen más allá de AECID) sin cambiar el frontend, solo el pipeline |

## 8. Lo que necesitas decidir/traer tú a VSCode

- Confirmar si el proyecto Vue ya existe o arrancas desde cero (`npm create vite@latest`).
- Variable de entorno para la URL base de la API (`VITE_API_URL`), siguiendo el mismo patrón que WerkTax.
- El archivo `world.json` de topología: se puede sacar del propio paquete de ECharts (`echarts/map/json/world.json`) o de `world-atlas` en npm — confirmar cuál da mejor nivel de detalle para tus países LatAm/África prioritarios.
