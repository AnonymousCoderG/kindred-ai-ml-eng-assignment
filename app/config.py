from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+psycopg://kindred:kindred@localhost:5432/kindred"
    embed_dim: int = 16
    payment_timeout_trigger_cents: int = 999999

    # Part 3: real LLM extraction through any OpenAI-compatible chat API
    # (Groq, OpenRouter, Cerebras, Mistral, OpenAI, ...). Declared here so these
    # keys are accepted in .env (pydantic-settings rejects unknown keys).
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 30.0
    llm_max_attempts: int = 4
    llm_base_delay_seconds: float = 1.0
    llm_max_delay_seconds: float = 20.0


settings = Settings()