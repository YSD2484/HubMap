from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Class to store all the settings of the application."""

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    SERP_VELA_KEY: str = ""
    SERP_VELA_URL: str = ""
    MAX_PROFILES: int = 50000
    FOUNDER_DATA_BQ_CREDENTIALS: str = "/home/ysd2484/vela2/zihni-255523-3e68f4df273e.json"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"
    # Add your environment variables here and add them to the .env file

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @classmethod
    def customise_sources(
        cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customise the settings sources order.

        Order: dotenv, file secrets, environment variables, then initialization.
        """
        return (
            dotenv_settings,
            file_secret_settings,
            env_settings,
            init_settings,
        )


settings = Settings()
