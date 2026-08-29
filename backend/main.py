import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import (
    anios_disponibles,
    buscar_proyectos,
    detalle_pais,
    pais_por_anio,
    resumen_paises,
    resumen_por_anio,
    resumen_por_grupo,
    sectores_disponibles,
)

app = FastAPI(title="SigueElDinero API")

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = {"http://localhost:5173", FRONTEND_ORIGIN}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/paises/resumen")
def get_resumen(anio: int | None = None, grupo: str | None = None):
    return resumen_paises(anio=anio, grupo=grupo)


@app.get("/api/paises/{iso_alpha3}/detalle")
def get_detalle(iso_alpha3: str, anio: int | None = None):
    detalle = detalle_pais(iso_alpha3.upper(), anio=anio)
    if detalle is None:
        raise HTTPException(status_code=404, detail="Pais no encontrado")
    return detalle


@app.get("/api/paises/{iso_alpha3}/por-anio")
def get_pais_por_anio(iso_alpha3: str, grupo: str | None = None):
    datos = pais_por_anio(iso_alpha3.upper(), grupo=grupo)
    if datos is None:
        raise HTTPException(status_code=404, detail="Pais no encontrado")
    return datos


@app.get("/api/filtros/anios")
def get_anios():
    return anios_disponibles()


@app.get("/api/filtros/sectores")
def get_sectores():
    return sectores_disponibles()


@app.get("/api/resumen/por-anio")
def get_resumen_por_anio(grupo: str | None = None):
    return resumen_por_anio(grupo=grupo)


@app.get("/api/resumen/por-grupo")
def get_resumen_por_grupo(anio: int | None = None):
    return resumen_por_grupo(anio=anio)


@app.get("/api/proyectos/buscar")
def get_buscar_proyectos(
    q: str | None = None,
    anio: int | None = None,
    grupo: str | None = None,
    pais: str | None = None,
    pagina: int = 1,
    por_pagina: int = 30,
):
    return buscar_proyectos(q=q, anio=anio, grupo=grupo, pais=pais, pagina=pagina, por_pagina=por_pagina)
