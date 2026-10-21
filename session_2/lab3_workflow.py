"""
Lab 3: Orquestación Multi-Agente y Workflows (Microsoft Agent Framework)
------------------------------------------------------------------------
Objetivo:
  - Crear dos agentes especializados: Analista Forense y Planificador SRE.
  - Diseñar una herramienta de remediación con Human-in-the-Loop (approval_mode="always_require").
  - Ensamblar un Workflow determinista conectando ambos agentes mediante WorkflowBuilder.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Microsoft Agent Framework Imports
from agent_framework import Agent, WorkflowBuilder, tool
from agent_framework.openai import OpenAIChatClient

# Importar factoría de clientes LLM (Azure AI Foundry / Azure OpenAI / OpenAI)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from client_factory import get_chat_client
except ImportError:
    from ..client_factory import get_chat_client

load_dotenv()


# ============================================================================
# 1. Herramienta con Aprobación Humana Obligatoria (Human-in-the-Loop)
# ============================================================================
@tool(
    name="apply_cluster_remediation",
    description="Aplica cambios directos de remediación o comandos kubectl en el clúster de producción.",
    approval_mode="always_require"  # <- Compuerta nativa HITL de Microsoft Agent Framework
)
def apply_cluster_remediation(service_name: str, action_command: str) -> str:
    """Ejecuta una acción sobre la infraestructura.

    Requiere aprobación explícita de un operador antes de ejecutarse.
    """
    return (
        f"[ACCIÓN APLICADA CON ÉXITO] Servicio: {service_name}\n"
        f"Comando ejecutado en clúster: '{action_command}'\n"
        f"Estado: Pods reiniciados y tráfico restaurado satisfactoriamente."
    )


# ============================================================================
# 2. Factoría de Agentes Especializados
# ============================================================================
def create_specialized_agents(model_name: str | None = None):
    """Crea los agentes especializados conectando a Azure AI Foundry, Azure OpenAI u OpenAI."""
    client = get_chat_client(model_name)

    # Agente 1: Analista de Incidentes (Especialista en extracción y diagnóstico)
    log_analyst = Agent(
        name="LogAnalystAgent",
        client=client,
        instructions=(
            "Eres un analista forense de incidentes de software. "
            "Tu tarea es analizar los logs sin procesar recibidos y extraer: "
            "1. Nombre del servicio afectado. "
            "2. Causa raíz técnica (Out of Memory, Timeout, Deadlock, etc.). "
            "3. Severidad del incidente: 'CRITICAL' o 'NORMAL'. "
            "Entrega un diagnóstico conciso y técnico para el ingeniero de remediación."
        )
    )

    # Agente 2: Ingeniero de Remediación (Especialista en infraestructura K8s)
    remediation_planner = Agent(
        name="RemediationPlannerAgent",
        client=client,
        instructions=(
            "Eres un ingeniero de infraestructura Kubernetes. "
            "Recibes el diagnóstico de un incidente y debes proponer un plan de acción concreto. "
            "Si la severidad es CRITICAL o requiere cambios en el clúster, invoca la herramienta "
            "'apply_cluster_remediation' con el comando kubectl adecuado para mitigar el problema."
        ),
        tools=[apply_cluster_remediation]
    )

    return log_analyst, remediation_planner


# ============================================================================
# 3. Ensamblado del Workflow (Pipes & Filters)
# ============================================================================
def build_incident_workflow():
    """Construye el grafo del flujo de trabajo conectando los dos agentes."""
    log_analyst, remediation_planner = create_specialized_agents()

    # WorkflowBuilder inicializado con el nodo de entrada
    builder = WorkflowBuilder(start_executor=log_analyst)
    
    # Conectamos la salida del Analista a la entrada del Remediador
    builder.add_edge(log_analyst, remediation_planner)
    
    workflow = builder.build()
    return workflow, log_analyst, remediation_planner


# ============================================================================
# 4. Demostración por Consola
# ============================================================================
async def run_pipeline():
    print("=" * 75)
    print("🔄  Microsoft Agent Framework - Lab 3: Multi-Agent Workflow Pipeline")
    print("=" * 75)

    workflow, log_analyst, remediation_planner = build_incident_workflow()

    critical_incident_log = (
        "2026-09-28T04:12:08.102Z [ERROR] auth-service-7d84b8c8d5-w2k9q: "
        "java.lang.OutOfMemoryError: Java heap space exceeded in JWTValidationFilter. "
        "Process terminated with exit code 137 (OOMKilled). "
        "Pod status: CrashLoopBackOff. Consecutive failures: 6."
    )

    print("\n📄 Log de Incidente a Ingestar:")
    print("-" * 50)
    print(critical_incident_log)
    print("-" * 50)
    print("\n🚀 Iniciando Pipeline [LogAnalystAgent -> RemediationPlannerAgent]...")

    try:
        result = await workflow.run(critical_incident_log)
        print("\n✅ Pipeline finalizado.")
        print("Trazas de eventos capturados:")
        for event in result:
            print(f"  - Evento: {getattr(event, 'type', str(event))}")
    except Exception as ex:
        print(f"\n❌ Error al ejecutar el workflow: {ex}")
        print("Verifica tu clave de API en el archivo .env.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
