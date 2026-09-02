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

-- Fase 2: concesiones BDNS agregadas por comunidad autonoma.
create table if not exists dim_ccaa (
    ccaa_id       serial primary key,
    codigo_ine    varchar(2) unique not null,
    nombre        text not null
);

insert into dim_ccaa (codigo_ine, nombre) values
    ('01', 'Andalucía'),
    ('02', 'Aragón'),
    ('03', 'Principado de Asturias'),
    ('04', 'Illes Balears'),
    ('05', 'Canarias'),
    ('06', 'Cantabria'),
    ('07', 'Castilla y León'),
    ('08', 'Castilla-La Mancha'),
    ('09', 'Cataluña'),
    ('10', 'Comunitat Valenciana'),
    ('11', 'Extremadura'),
    ('12', 'Galicia'),
    ('13', 'Comunidad de Madrid'),
    ('14', 'Región de Murcia'),
    ('15', 'Comunidad Foral de Navarra'),
    ('16', 'País Vasco'),
    ('17', 'La Rioja'),
    ('18', 'Ceuta'),
    ('19', 'Melilla')
on conflict (codigo_ine) do nothing;

create table if not exists fact_gasto_ccaa (
    ccaa_id             int references dim_ccaa(ccaa_id),
    anio                int not null,
    mes                 int not null,
    importe_total_eur   numeric(16,2) not null,
    n_concesiones       int not null,
    fecha_actualizacion timestamptz default now(),
    primary key (ccaa_id, anio, mes)
);

create table if not exists fact_gasto_ccaa_organismo (
    ccaa_id             int references dim_ccaa(ccaa_id),
    anio                int not null,
    mes                 int not null,
    organismo           text not null,
    importe_total_eur   numeric(16,2) not null,
    n_concesiones       int not null,
    primary key (ccaa_id, anio, mes, organismo)
);

-- Concesiones de BDNS otorgadas directamente por AECID, no publicadas todavia en IATI (fact_gasto).
-- Sin FK a dim_pais a proposito: un pais puede aparecer primero por esta via, antes de tener
-- ninguna actividad IATI. Nunca se mezcla con fact_gasto -- ver
-- docs/superpowers/specs/2026-09-01-adelanto-aecid-bdns-design.md.
create table if not exists fact_gasto_aecid_bdns (
    concesion_id        bigint primary key,        -- id de BDNS, natural key
    numero_convocatoria text not null,              -- para el dedup contra fact_gasto.url_bdns
    iso_alpha3          varchar(3),                 -- null si no se identifico un unico pais
    beneficiario        text,
    titulo              text,                       -- campo "convocatoria" de BDNS
    importe_eur         numeric(14,2) not null,
    fecha_concesion      date,
    fecha_ingesta        timestamptz default now()
);
create index if not exists idx_aecid_bdns_pais on fact_gasto_aecid_bdns(iso_alpha3);