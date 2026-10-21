# 🧪 Guía Práctica de Laboratorios: Microsoft Agent Framework & DevUI

Esta guía contiene el código de referencia completo, explicaciones paso a paso y comandos de validación para los 4 laboratorios de la capacitación.

---

## ⚙️ Entorno y Preparación Rápida

### 1. Inicialización del Proyecto (con `uv` o `pip`)

```bash
# Opción A: Usando uv (recomendado, ultra rápido)
uv init demos-maf
cd demos-maf
uv venv .venv
source .venv/bin/activate
uv pip install agent-framework agent-framework-devui pydantic python-dotenv

# Opción B: Usando pip tradicional
python3 -m venv .venv
source .venv/bin/activate
pip install agent-framework agent-framework-devui pydantic python-dotenv
```

### 2. Archivo de Variables de Entorno (`.env`)
Crea o edita el archivo `.env` en la raíz del proyecto. Soporta Azure AI Foundry, Azure OpenAI o OpenAI estándar:
```env
# Opción 1: Azure AI Foundry (Recomendado)
AI_FOUNDRY_API_KEY=tu-clave-de-foundry
AI_FOUNDRY_ENDPOINT=https://tu-recurso.services.ai.azure.com/models
AI_FOUNDRY_MODEL=gpt-4o-mini

# Opción 2: Azure OpenAI Service
# AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
# AZURE_OPENAI_API_KEY=tu-clave
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Opción 3: OpenAI Directo
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# Puerto para DevUI (por defecto 8090)
DEVUI_PORT=8090
```

---

## 📌 SESIÓN 1

### Lab 1: Construcción de un Agente Tipado con Tools
* **Archivo:** `session_1/lab1_single_agent.py`
* **Objetivo:** Definir contratos estrictos con `Pydantic` e instanciar un agente capaz de invocar funciones de infraestructura de forma segura.

```python
"""
Lab 1: Agente Autónomo con Function Calling Tipado (Microsoft Agent Framework)
"""
import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Microsoft Agent Framework
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatClient

load_dotenv()

# 1. Contrato de Datos (Data Contract)
class ServiceHealthQuery(BaseModel):
    service_name: str = Field(description="Nombre del microservicio a inspeccionar")
    environment: str = Field(default="production", description="Entorno: 'production' o 'staging'")
    include_metrics: bool = Field(default=True, description="Incluir métricas de CPU/Memoria")

# 2. Definición de la Tool
@tool(name="inspect_service_health", description="Consulta telemetría de pods de un servicio.")
def inspect_service_health(query: ServiceHealthQuery) -> str:
    svc = query.service_name.lower()
    if "auth" in svc:
        return f"[ALERTA] Ambiente: {query.environment.upper()} - {query.service_name}: 2/5 pods en CrashLoopBackOff (OOMKilled)."
    return f"[OK] Ambiente: {query.environment.upper()} - {query.service_name}: 3/3 pods saludables."

# 3. Factoría del Agente (Soporta Azure AI Foundry, Azure OpenAI y OpenAI)
def create_sre_agent() -> Agent:
    client = get_chat_client()
    return Agent(
        name="SREDiagnosticAgent",
        client=client,
        instructions="Eres un Staff SRE. Diagnostica incidentes usando tus tools e indica causa raíz y mitigación.",
        tools=[inspect_service_health]
    )

async def main():
    agent = create_sre_agent()
    response = await agent.run("¿Puedes revisar qué le pasa a auth-service en producción?")
    print(response.text if hasattr(response, "text") else response)

if __name__ == "__main__":
    asyncio.run(main())
```

* **Punto de Inspección:** Ejecutar con `python session_1/lab1_single_agent.py`. Observar cómo el agente detecta que la pregunta requiere invocar `inspect_service_health`, valida los argumentos según `ServiceHealthQuery` y sintetiza el reporte final.

---

### Lab 2: Montaje y Depuración en DevUI
* **Archivo:** `session_1/lab2_devui_serve.py`
* **Objetivo:** Exponer el agente en **DevUI** para inspeccionar llamadas a herramientas, tokens y respuestas interactivas.

```python
"""
Lab 2: Inspección y Pruebas en DevUI
Levanta el harness de desarrollo en localhost:8090
"""
import os
import sys
from dotenv import load_dotenv
from agent_framework.devui import serve

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lab1_single_agent import create_sre_agent

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("DEVUI_PORT", "8090"))
    agent = create_sre_agent()
    
    print(f"🚀 Iniciando DevUI en http://localhost:{port} ...")
    serve(
        entities=[agent],
        port=port,
        host="127.0.0.1",
        auth_enabled=False
    )
```

* **Validación en DevUI:**
  1. Abrir `http://localhost:8090` en el navegador.
  2. Seleccionar el agente `SREDiagnosticAgent` en el selector lateral.
  3. Probar enviando:
     * `"Revisa el estado de auth-service en producción"` $\rightarrow$ Abrir el panel de eventos a la derecha para ver los argumentos JSON exactos enviados a la tool.
     * `"¿Qué recetas de pizza recomiendas?"` $\rightarrow$ Observar cómo el agente razona que no tiene herramientas culinarias y declina la solicitud.
  4. En una terminal secundaria, probar el endpoint de API generado por DevUI:
     ```bash
     curl -X POST http://localhost:8090/v1/chat/completions \
       -H "Content-Type: application/json" \
       -d '{"messages": [{"role": "user", "content": "Verifica payments-api en staging"}]}'
     ```

---

## 📌 SESIÓN 2

### Lab 3: Orquestación de Workflow Secuencial con HITL
* **Archivo:** `session_2/lab3_workflow.py`
* **Objetivo:** Implementar un pipeline con dos agentes especializados y una compuerta de aprobación humana (*Human-in-the-Loop*).

```python
"""
Lab 3: Pipeline Multi-Agente con Compuerta de Aprobación Humana (HITL)
Patrón: Pipes & Filters con Tool de Aprobación Obligatoria.
"""
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Agent, WorkflowBuilder, tool
from agent_framework.openai import OpenAIChatClient

load_dotenv()

# 1. Herramienta con Aprobación Humana Obligatoria (HITL)
@tool(
    name="apply_cluster_remediation",
    description="Aplica cambios directos o comandos kubectl en el clúster.",
    approval_mode="always_require"  # <- Compuerta nativa HITL
)
def apply_cluster_remediation(service_name: str, action_command: str) -> str:
    return f"[ACCIÓN APLICADA] Servicio: {service_name}, Comando: '{action_command}'. Pods reiniciados."

# 2. Factoría de Agentes Especializados (Soporta Azure AI Foundry, Azure OpenAI y OpenAI)
def create_specialized_agents():
    client = get_chat_client()
    log_analyst = Agent(
        name="LogAnalystAgent",
        client=client,
        instructions="Analiza logs de error y extrae servicio, causa raíz y severidad ('CRITICAL' o 'NORMAL')."
    )
    remediation_planner = Agent(
        name="RemediationPlannerAgent",
        client=client,
        instructions="Genera comandos de mitigación K8s. Si es CRITICAL, ejecuta 'apply_cluster_remediation'.",
        tools=[apply_cluster_remediation]
    )
    return log_analyst, remediation_planner

# 3. Ensamblado del Workflow
def build_incident_workflow():
    log_analyst, remediation_planner = create_specialized_agents()
    builder = WorkflowBuilder(start_executor=log_analyst)
    builder.add_edge(log_analyst, remediation_planner)
    return builder.build(), log_analyst, remediation_planner

async def main():
    workflow, _, _ = build_incident_workflow()
    log = "2026-09-28 auth-service: java.lang.OutOfMemoryError (OOMKilled). Pods in CrashLoopBackOff."
    res = await workflow.run(log)
    print("Workflow ejecutado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Lab 4: Visualización de Grafos y Trazas en DevUI
* **Archivo:** `session_2/lab4_multiagent_devui.py`
* **Objetivo:** Registrar el workflow orquestado en **DevUI** para inspeccionar la máquina de estados, aprobar ejecuciones pausadas y analizar trazas de rendimiento.

```python
"""
Lab 4: Servir el Workflow Multi-Agente en DevUI
"""
import os
import sys
from dotenv import load_dotenv
from agent_framework.devui import serve

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lab3_workflow import build_incident_workflow

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("DEVUI_PORT", "8090"))
    workflow, log_analyst, remediation_planner = build_incident_workflow()
    
    print(f"🚀 Montando Workflow en DevUI en http://localhost:{port} ...")
    serve(
        entities=[workflow, log_analyst, remediation_planner],
        port=port,
        host="127.0.0.1",
        auth_enabled=False
    )
```

* **Validación en DevUI (Lab 4):**
  1. Abrir `http://localhost:8090`.
  2. En el menú superior o lateral, seleccionar la pestaña **Workflows** y elegir `IncidentRemediationPipeline`.
  3. Visualizar el diagrama de nodos: `analyze` $\rightarrow$ `gate` $\rightarrow$ `remediate`.
  4. Ejecutar el flujo con los logs de ejemplo:
     * Observar cómo el nodo `analyze` se ilumina y procesa el texto.
     * Observar cómo la ejecución se pausa en el nodo `gate` mostrando el diálogo de interacción humana:
       * Botón de aprobación con opción de inyectar feedback: *"Aprobado por SRE de guardia"*.
     * Al hacer clic en confirmar, el workflow se reanuda y el nodo `remediate` genera el script final con las instrucciones de mitigación.
  5. Ir a la pestaña **Traces / OpenTelemetry** en DevUI y revisar los spans de tiempo de cada llamada a la API y el desglose de tokens utilizados.
