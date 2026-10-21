"""
client_factory.py - Factoría unificada de clientes LLM para Microsoft Agent Framework
-------------------------------------------------------------------------------------
Soporta resolución transparente de proveedores en el siguiente orden de precedencia:
  1. Azure AI Foundry (AI_FOUNDRY_API_KEY, AI_FOUNDRY_ENDPOINT, AI_FOUNDRY_MODEL)
  2. Azure OpenAI Service (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT)
  3. OpenAI Directo (OPENAI_API_KEY, OPENAI_MODEL)
"""
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient

load_dotenv()


def get_chat_client(model_name: str | None = None):
    """Instancia y retorna un ChatClient configurado según las variables de entorno disponibles."""
    # 1. Azure AI Foundry (Recomendado)
    ai_foundry_key = os.getenv("AI_FOUNDRY_API_KEY")
    ai_foundry_endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
    ai_foundry_model = model_name or os.getenv("AI_FOUNDRY_MODEL", "gpt-4o-mini")

    if ai_foundry_key and ai_foundry_endpoint and not ai_foundry_key.startswith("xxxxx"):
        endpoint = ai_foundry_endpoint.strip()

        # Caso A: Azure OpenAI tradicional (.openai.azure.com)
        if "openai.azure.com" in endpoint:
            return OpenAIChatClient(
                azure_endpoint=endpoint,
                api_key=ai_foundry_key,
                model=ai_foundry_model,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            )

        # Caso B: Endpoint de inferencia de Azure AI Foundry (services.ai.azure.com o models.ai.azure.com)
        # Utiliza OpenAIChatCompletionClient compatible con /chat/completions y header 'api-key'
        base_url = endpoint
        if "services.ai.azure.com" in endpoint and not endpoint.endswith("/models") and not endpoint.endswith("/v1"):
            base_url = f"{endpoint.rstrip('/')}/models"

        return OpenAIChatCompletionClient(
            base_url=base_url,
            api_key=ai_foundry_key,
            model=ai_foundry_model,
            default_headers={"api-key": ai_foundry_key},
        )

    # 2. Azure OpenAI tradicional
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    if azure_endpoint and azure_key:
        return OpenAIChatClient(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            model=azure_deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        )

    # 3. OpenAI Directo
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not openai_key or openai_key.startswith("sk-your-openai"):
        print("\n⚠️  [AVISO]: No se detectaron credenciales válidas en .env.")
        print("Configura AI_FOUNDRY_API_KEY y AI_FOUNDRY_ENDPOINT para conectar con Azure AI Foundry.\n")

    return OpenAIChatClient(
        model=openai_model,
        api_key=openai_key or "sk-dummy-key-for-initialization",
    )
