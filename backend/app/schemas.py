"""schemas.py - Pydantic models for ExamenesULM REST API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from enum import Enum


# ====================================================================
# Auth
# ====================================================================


class LoginRequest(BaseModel):
    nifPasaporte: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    exitoso: bool
    requiereMFA: bool = False
    mensaje: Optional[str] = None
    tokenTemporal: Optional[str] = None
    jwtToken: Optional[str] = None


class VerifyMfaRequest(BaseModel):
    nifPasaporte: str
    codigoMfa: str


# ====================================================================
# Examen (selección)
# ====================================================================


class ExamenDTO(BaseModel):
    sessionId: str
    estado: int           # 0=NP, 1=INICIADO, 2=COMPROBADO, 3=FINALIZADO
    codModulo: str
    moduloDescricao: str
    titulo: str
    nTest: int
    tTestSegundos: int
    fechaExamen: Optional[str] = None


# ====================================================================
# Respuesta individual de pregunta
# ====================================================================


class RespuestaPregunta(BaseModel):
    """Respuesta del alumno para una única pregunta."""
    numero: int           # orden_pregunta en el banco (orden_en_examen)
    banco_id: int         # id de la pregunta en preguntas_banco
    respuesta: str        # '', 'A', 'B', 'C' o 'D' (mayúscula)
    impugnacion: Optional[str] = None


# ====================================================================
# Finalizar examen — entrada desde frontend
# ====================================================================


class FinalizarRequest(BaseModel):
    """Schema que recibe el frontend al finalizar un examen."""
    examId: str
    sessionID: str
    nifPasaporte: str
    respuestas: list[RespuestaPregunta]
    tiempoRestante: int
    totalTiempo: int = 0


# ====================================================================
# Resultado interno (scoring) — lo que devuelve la función de cálculo
# ====================================================================


class ResultadoCalculo(BaseModel):
    """Resultado interno devuelto tras calcular scoring + persistencia."""
    correctas: int
    fallos: int
    no_contestadas: int
    porcentaje_acierto: float
    es_apto: bool
    nota_final: Optional[float] = None


# ====================================================================
# FinalizarResponse — respuesta del endpoint POST /finalizar
# ====================================================================


class FinalizarResponse(BaseModel):
    exitoso: bool
    mensaje: str
    resultados: ResultadoCalculo


# ====================================================================
# Resultados examen — lectura desde DB (tabla resultados_examen)
# 
# Columnas SQL Server  → Pydantic
# ────────────────────   ──────────────────────
# id                   int (bigint auto-increment PK)
# examen_id            int (bigint FK → examenes.id)
# correctas            int NOT NULL
# fallos               int NOT NULL
# no_contestadas       int NOT NULL
# porcentaje_acierto   decimal(5,2) → float
# es_apto              bit → bool
# nota_final           decimal(5,2) → Optional[float] | None
# mensaje_resultado    nvarchar(200) NOT NULL
# fecha_calculo        datetime2(3) → str ISO-8601 UTC
# respuestas_json      nvarchar(max) → Optional[str] | None
# tiempo_restante_segundos  int (nullable)
# tiempo_total_segundos     int (nullable)
# alumno_id            int (nullable)
# ====================================================================


class ResultadoExamenRead(BaseModel):
    """DTO que devuelve el resultado final de un examen desde BD."""

    id: Optional[int] = None
    examen_id: int
    correctas: int
    fallos: int
    no_contestadas: int
    porcentaje_acierto: float
    es_apto: bool
    nota_final: Optional[float] = None
    mensaje_resultado: str
    fecha_calculo: str  # ISO-8601 datetime UTC
    respuestas_json: Optional[str] = None
    tiempo_restante_segundos: Optional[int] = None
    tiempo_total_segundos: Optional[int] = None
    alumno_id: Optional[int] = None


# Alias backward-compatible para rutas que ya lo usan
ResultadoResponse = ResultadoExamenRead
