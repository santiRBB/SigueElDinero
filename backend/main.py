import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import anios_disponibles, detalle_pais, resumen_paises, sectores_disponibles

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
def get_resumen(anio: int | None = None, sector: str | None = None):
    return resumen_paises(anio=anio, sector=sector)


@app.get("/api/paises/{iso_alpha3}/detalle")
def get_detalle(iso_alpha3: str, anio: int | None = None):
    detalle = detalle_pais(iso_alpha3.upper(), anio=anio)
    if detalle is None:
        raise HTTPException(status_code=404, detail="Pais no encontrado")
    return detalle


@app.get("/api/filtros/anios")
def get_anios():
    return anios_disponibles()


@app.get("/api/filtros/sectores")
def get_sectores():
    return sectores_disponibles()
