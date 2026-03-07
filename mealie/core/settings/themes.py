from pydantic_settings import BaseSettings, SettingsConfigDict


class Theme(BaseSettings):
    light_primary: str = "#228B22"
    light_accent: str = "#2E7D32"
    light_secondary: str = "#1B5E20"
    light_success: str = "#43A047"
    light_info: str = "#1976D2"
    light_warning: str = "#FF6D00"
    light_error: str = "#EF5350"

    dark_primary: str = "#4CAF50"
    dark_accent: str = "#66BB6A"
    dark_secondary: str = "#2E7D32"
    dark_success: str = "#43A047"
    dark_info: str = "#1976D2"
    dark_warning: str = "#FF6D00"
    dark_error: str = "#EF5350"
    model_config = SettingsConfigDict(env_prefix="theme_", extra="allow")
