"""Orquestación Pipes and Filters del procesamiento de un PDF.

- Filtro: unidad pura (`process(data) -> data`) que no conoce a sus vecinos
  ni al orquestador. OpenFilter, DetectFilter y SplitFilter son los tres
  filtros de esta app; cada uno se puede instanciar y probar en aislamiento.
- Pipe: conecta un filtro con el siguiente y observa el paso (logging o
  progreso) sin que el filtro sepa que está siendo observado.
- Pipeline: encadena filtros vía pipes; es el único componente que conoce el
  orden completo.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import pymupdf as fitz

from pdfsplitter.extractor import OpenFilter
from pdfsplitter.detector import DetectFilter
from pdfsplitter.models import Chapter
from pdfsplitter.settings import PipelineSettings
from pdfsplitter.splitter import SplitFilter


@dataclass
class PipelineData:
    """El paquete de datos que fluye por los pipes entre filtros."""

    input_pdf: Path
    settings: PipelineSettings
    output_dir: Path
    document: fitz.Document | None = None
    chapters: list[Chapter] = field(default_factory=list)
    generated_files: list[Path] = field(default_factory=list)

    def close(self) -> None:
        if self.document is not None:
            self.document.close()
            self.document = None


class ProgressReporter(Protocol):
    """Observador de la ejecución del pipeline, ajeno a los filtros."""

    def stage(self, name: str) -> None: ...
    def log(self, level: str, message: str) -> None: ...


class NullProgressReporter:
    """Reporter que no hace nada, útil para pruebas o uso programático."""

    def stage(self, name: str) -> None:
        pass

    def log(self, level: str, message: str) -> None:
        pass


class Filter(Protocol):
    """Unidad pura: transforma PipelineData, no conoce el resto del pipeline."""

    name: str

    def process(self, data: PipelineData) -> PipelineData: ...


class Pipe:
    """Conecta un filtro con el siguiente, observando el paso sin alterarlo."""

    def __init__(self, filter_: Filter, report: ProgressReporter) -> None:
        self._filter = filter_
        self._report = report

    def __call__(self, data: PipelineData) -> PipelineData:
        self._report.stage(self._filter.name)
        return self._filter.process(data)


class Pipeline:
    """Encadena filtros vía pipes; es el único que conoce el orden completo."""

    def __init__(self, filters: Sequence[Filter]) -> None:
        self._filters = list(filters)

    def run(self, data: PipelineData, report: ProgressReporter | None = None) -> PipelineData:
        report = report or NullProgressReporter()
        for filter_ in self._filters:
            data = Pipe(filter_, report)(data)
        return data


def default_pipeline() -> Pipeline:
    """Pipeline estándar: abrir → detectar capítulos → exportar."""
    return Pipeline([OpenFilter(), DetectFilter(), SplitFilter()])


def detect_pipeline() -> Pipeline:
    """Solo abre y detecta: para previsualizar capítulos sin escribir nada a disco."""
    return Pipeline([OpenFilter(), DetectFilter()])


def export_pipeline() -> Pipeline:
    """Abre y exporta capítulos ya elegidos de antemano (p. ej. desde una vista
    previa editada por el usuario), sin volver a correr la detección."""
    return Pipeline([OpenFilter(), SplitFilter()])
