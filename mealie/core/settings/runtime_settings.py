"""Runtime settings storage for Mealie.

This module provides functionality to store and retrieve runtime-changeable settings
that don't require a container restart, such as the selected LLM model.
"""

import json
from pathlib import Path

from pydantic import BaseModel

from mealie.core import root_logger

logger = root_logger.get_logger(__name__)


class RuntimeSettings(BaseModel):
    """Settings that can be changed at runtime without container restart."""

    llm_model: str | None = None
    """The LLM model to use for OpenAI/LiteLLM requests. If None, uses the default from env."""


class RuntimeSettingsService:
    """Service for managing runtime-changeable settings."""

    def __init__(self, data_dir: Path):
        self.settings_file = data_dir / "runtime_settings.json"
        self._settings: RuntimeSettings | None = None

    def _load_settings(self) -> RuntimeSettings:
        """Load settings from file, or return defaults if file doesn't exist."""
        if self._settings is not None:
            return self._settings

        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    data = json.load(f)
                self._settings = RuntimeSettings(**data)
                logger.debug(f"Loaded runtime settings from {self.settings_file}")
            except Exception as e:
                logger.warning(f"Failed to load runtime settings: {e}. Using defaults.")
                self._settings = RuntimeSettings()
        else:
            self._settings = RuntimeSettings()

        return self._settings

    def _save_settings(self, settings: RuntimeSettings) -> None:
        """Save settings to file."""
        try:
            # Ensure parent directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.settings_file, "w") as f:
                json.dump(settings.model_dump(), f, indent=2)

            self._settings = settings
            logger.debug(f"Saved runtime settings to {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save runtime settings: {e}")
            raise

    def get_settings(self) -> RuntimeSettings:
        """Get current runtime settings."""
        return self._load_settings()

    def get_llm_model(self) -> str | None:
        """Get the configured LLM model, or None if using default."""
        settings = self._load_settings()
        return settings.llm_model

    def set_llm_model(self, model: str | None) -> None:
        """Set the LLM model to use."""
        settings = self._load_settings()
        settings.llm_model = model
        self._save_settings(settings)
        logger.info(f"LLM model set to: {model or 'default'}")


# Global instance - will be initialized by the app
_runtime_settings_service: RuntimeSettingsService | None = None


def init_runtime_settings(data_dir: Path) -> RuntimeSettingsService:
    """Initialize the runtime settings service."""
    global _runtime_settings_service
    _runtime_settings_service = RuntimeSettingsService(data_dir)
    return _runtime_settings_service


def get_runtime_settings() -> RuntimeSettingsService:
    """Get the runtime settings service instance."""
    if _runtime_settings_service is None:
        raise RuntimeError("Runtime settings service not initialized. Call init_runtime_settings() first.")
    return _runtime_settings_service
