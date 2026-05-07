from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class FrameworkDetectionResult:
    changed_files: list[str]
    extensions: list[str]
    ecosystems: list[str]
    signals: dict[str, list[str]]


class FrameworkDetector:
    """Detect review ecosystems from changed file paths without reading repo internals."""

    _ECOSYSTEM_ORDER = ["python", "typescript_angular", "dotnet", "java_springboot"]

    _PYTHON_EXTENSIONS = {".py", ".pyi"}
    _PYTHON_FILES = {
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "pipfile",
        "pipfile.lock",
        "tox.ini",
        "setup.py",
        "setup.cfg",
    }

    _TYPESCRIPT_EXTENSIONS = {".ts", ".tsx"}
    _FRONTEND_TEMPLATE_EXTENSIONS = {".html", ".scss", ".sass", ".css"}
    _TYPESCRIPT_FILES = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "tsconfig.json",
        "angular.json",
    }

    _DOTNET_EXTENSIONS = {".cs", ".csproj", ".sln", ".fs", ".fsproj", ".vb", ".vbproj", ".cshtml"}
    _DOTNET_FILES = {"global.json", "nuget.config", "directory.build.props", "directory.build.targets"}

    _JAVA_EXTENSIONS = {".java"}
    _JAVA_FILES = {
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "gradle.properties",
    }
    _SPRING_CONFIG_FILES = {"application.yml", "application.yaml", "application.properties"}

    def detect(self, changed_files: Iterable[str]) -> FrameworkDetectionResult:
        normalized_files = sorted({self._normalize_path(path) for path in changed_files if str(path).strip()})
        extensions = sorted({PurePosixPath(path).suffix.lower() for path in normalized_files if PurePosixPath(path).suffix})

        signals: dict[str, list[str]] = {key: [] for key in self._ECOSYSTEM_ORDER}

        for path in normalized_files:
            lower_path = path.lower()
            name = PurePosixPath(lower_path).name
            suffix = PurePosixPath(lower_path).suffix

            if suffix in self._PYTHON_EXTENSIONS or name in self._PYTHON_FILES:
                signals["python"].append(path)

            if self._is_typescript_angular_signal(lower_path, name, suffix):
                signals["typescript_angular"].append(path)

            if suffix in self._DOTNET_EXTENSIONS or name in self._DOTNET_FILES or name.endswith((".props", ".targets")):
                signals["dotnet"].append(path)

            if suffix in self._JAVA_EXTENSIONS or name in self._JAVA_FILES:
                signals["java_springboot"].append(path)

        # Spring config is only treated as Java/Spring evidence when the PR already has a Java build/code signal.
        if signals["java_springboot"]:
            for path in normalized_files:
                name = PurePosixPath(path.lower()).name
                if name in self._SPRING_CONFIG_FILES:
                    signals["java_springboot"].append(path)

        deduped_signals = {key: sorted(set(value)) for key, value in signals.items() if value}
        ecosystems = [key for key in self._ECOSYSTEM_ORDER if key in deduped_signals]

        return FrameworkDetectionResult(
            changed_files=normalized_files,
            extensions=extensions,
            ecosystems=ecosystems,
            signals=deduped_signals,
        )

    def _is_typescript_angular_signal(self, path: str, name: str, suffix: str) -> bool:
        if suffix in self._TYPESCRIPT_EXTENSIONS or name in self._TYPESCRIPT_FILES:
            return True
        if name.endswith((".component.html", ".component.scss", ".component.sass", ".component.css")):
            return True
        return "angular.json" in path or "/src/app/" in path and suffix in self._FRONTEND_TEMPLATE_EXTENSIONS

    @staticmethod
    def _normalize_path(path: str) -> str:
        return str(path).replace("\\", "/").strip()
