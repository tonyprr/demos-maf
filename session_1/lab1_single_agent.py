"""
Lab 1: Agente Autónomo con Function Calling Tipado (Microsoft Agent Framework)
-----------------------------------------------------------------------------
Objetivo:
  - Definir un Data Contract estricto con Pydantic para herramientas de infraestructura.
  - Instanciar un Agente con ChatClient (OpenAI / Azure OpenAI).
  - Ejecutar el Reasoning Loop observando la invocación de herramientas y tipado.
"""
import os
import sys
import asyncio
from typing import Annotated
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Microsoft Agent Framework Imports
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatClient

# Importar factoría de clientes LLM (Azure AI Foundry / Azure OpenAI / OpenAI)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from client_factory import get_chat_client
except ImportError:
    from ..client_factory import get_chat_client

load_dotenv()


# ============================================================================
# 1. Contrato de Datos (Data Contract) con Pydantic
# ============================================================================
class ServiceHealthQuery(BaseModel):
    """Esquema de parámetros que el LLM debe cumplir obligatoriamente."""
    service_name: str = Field(
        description="Nombre del microservicio a inspeccionar (ej: auth-service, payments-api, orders-service)"
    )
    environment: str = Field(
        default="production",
        description="Entorno de despliegue: 'production', 'staging' o 'development'"
    )
    include_metrics: bool = Field(
        default=True,
        description="Indica si se deben adjuntar métricas de CPU y Memoria del clúster"
    )


# ============================================================================
# 2. Definición de la Tool (Función de Negocio con validación)
# ============================================================================
@tool(
    name="inspect_service_health",
    description="Consulta la telemetría en tiempo real de los pods y estado de salud de un microservicio."
)
def inspect_service_health(query: ServiceHealthQuery) -> str:
    """Simula una consulta a Prometheus o Kubernetes API."""
    if isinstance(query, dict):
        query = ServiceHealthQuery(**query)

    svc = query.service_name.lower()
    env = query.environment.lower()

    if "auth" in svc:
        return (
            f"[ALERTA KUBERNETES] Ambiente: {env.upper()}\n"
            f"Servicio: {query.service_name}\n"
            f"Estado: DEGRADADO - 2 de 5 pods en estado 'CrashLoopBackOff'.\n"
            f"Último Evento: OOMKilled (Out of Memory) en réplicas auth-pod-7b9d-4.\n"
            f"Consumo de Memoria: 98.4% del límite asignado (512MiB)."
        )
    elif "pay" in svc:
        return (
            f"[INFO KUBERNETES] Ambiente: {env.upper()}\n"
            f"Servicio: {query.service_name}\n"
            f"Estado: SALUDABLE - 3/3 pods en estado 'Running'.\n"
            f"Latencia p99: 45ms. Tasa de errores: 0.01%."
        )
    else:
        return (
            f"[INFO KUBERNETES] Ambiente: {env.upper()}\n"
            f"Servicio: {query.service_name}\n"
            f"Estado: OPERACIONAL - 2/2 pods saludables. Sin incidentes activos."
        )


# ============================================================================
# 3. Factoría del Agente SRE
# ============================================================================
def create_sre_agent(model_name: str | None = None) -> Agent:
    """Crea y configura la instancia del agente de diagnóstico SRE.
    
    Conecta automáticamente al modelo desplegado en Azure AI Foundry,
    Azure OpenAI o OpenAI según las variables de entorno configuradas.
    """
    client = get_chat_client(model_name)

    instructions = (
        "Eres un Staff Site Reliability Engineer (SRE) en un entorno de microservicios distribuidos. "
        "Tu misión es diagnosticar problemas en los servicios utilizando exclusivamente las herramientas "
        "de consulta técnica provistas. "
        "Siempre debes responder con: "
        "1. Diagnóstico del estado del servicio. "
        "2. Causa raíz identificada. "
        "3. Recomendación técnica de mitigación inmediata para el equipo de desarrollo."
    )

    return Agent(
        name="SREDiagnosticAgent",
        client=client,
        instructions=instructions,
        tools=[inspect_service_health]
    )


# ============================================================================
# 4. Función de Prueba por Consola
# ============================================================================
async def run_diagnostics():
    print("=" * 70)
    print("🛠️  Microsoft Agent Framework - Lab 1: Single Agent & Tool Calling")
    print("=" * 70)

    agent = create_sre_agent()

    query = "¿Puedes revisar qué le está pasando a auth-service en producción? Parece que hay caídas."
    print(f"\n👤 Usuario: {query}\n")
    print("🤖 Agente procesando (Reasoning Loop)...")

    try:
        response = await agent.run(query)
        print("\n" + "=" * 70)
        print("📋 Respuesta del Agente:")
        print("=" * 70)
        # response.messages o response.text
        if hasattr(response, "text"):
            print(response.text)
        else:
            print(str(response))
    except Exception as ex:
        print(f"\n❌ Error al ejecutar el agente: {ex}")
        print("Verifica tu clave de API en el archivo .env.")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
