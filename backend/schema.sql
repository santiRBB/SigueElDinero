-- Esquema SigueElDinero: gasto de cooperacion internacional (fuente: IATI / AECID)
-- Pensado para Supabase (Postgres). Ejecutar una vez, en el SQL editor de Supabase
-- o via psql contra tu DATABASE_URL.

create table if not exists dim_pais (
    pais_id       serial primary key,
    iso_alpha2    varchar(2) unique not null,
    iso_alpha3    varchar(3) unique,
    nombre        text not null,
    region        text
);

create table if not exists dim_categoria (
    categoria_id      serial primary key,
    codigo_crs        varchar(6) unique not null,   -- codigo OECD-DAC CRS de 5 digitos
    nombre            text,
    nombre_fuente     text                            -- 'publicador' | 'codelist_crs'
);

create table if not exists dim_organismo (
    organismo_id   serial primary key,
    nombre         text unique not null,
    tipo           text default 'ejecutor'            -- ejecutor | reportante | receptor
);

create table if not exists fact_gasto (
    gasto_id            bigserial primary key,
    aid                 text not null,                -- IATI identifier de la actividad
    pais_id             int references dim_pais(pais_id),
    categoria_id        int references dim_categoria(categoria_id),
    organismo_id        int references dim_organismo(organismo_id),
    titulo              text,
    descripcion         text,
    reporting_org       text,
    fuente              text default 'IATI',           -- IATI | BDNS | IGAE | BOE (futuras fuentes)
    reporting_ref       text,                           -- codigo IATI del organismo donante (ej. XM-DAC-50-21)
    activity_status     text,
    start_date          date,
    end_date            date,
    importe_total_eur   numeric(14,2),
    porcentaje_pais     numeric(6,3),
    porcentaje_fuente   text,                           -- 'declared' | 'assumed_equal_split'
    importe_pais_eur    numeric(14,2),
    tipo_transaccion    text,                           -- disbursement | commitment | null
    url_fuente          text,                           -- enlace directo a la ficha oficial (AECID, BDNS...)
    url_bdns            text,                           -- enlace a la convocatoria BDNS (subvenciones), si existe
    bdns_tipo_convocatoria text,                         -- tipo de convocatoria BDNS, verbatim de su API (ej. "Concurrencia competitiva - canonica")
    fecha_ingesta       timestamptz default now(),
    unique (aid, pais_id)                               -- evita duplicados si se re-ejecuta la carga
);

create index if not exists idx_fact_gasto_pais on fact_gasto(pais_id);
create index if not exists idx_fact_gasto_categoria on fact_gasto(categoria_id);
create index if not exists idx_fact_gasto_anio on fact_gasto(start_date);

-- Migracion idempotente para bases ya creadas antes de anadir url_bdns/bdns_tipo_convocatoria.
alter table fact_gasto add column if not exists url_bdns text;
alter table fact_gasto add column if not exists bdns_tipo_convocatoria text;