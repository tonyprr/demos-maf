"""
Lab 4: Visualización de Grafos y Trazas en DevUI (Microsoft Agent Framework)
--------------------------------------------------------------------------
Objetivo:
  - Servir el Workflow multi-agente en DevUI.
  - Visualizar la interacción entre LogAnalystAgent y RemediationPlannerAgent.
  - Experimentar la compuerta de aprobación humana (HITL) directamente en el navegador.
  - Auditar la latencia y los tokens consumidos mediante las trazas integradas de OpenTelemetry.
"""
import os
import sys
from dotenv import load_dotenv

# Microsoft Agent Framework DevUI
from agent_framework.devui import serve

# Añadir directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lab3_workflow import build_incident_workflow
from devui_patch import apply_devui_patches

load_dotenv()


def main():
    apply_devui_patches()
    port = int(os.getenv("DEVUI_PORT", "8090"))
    workflow, log_analyst, remediation_planner = build_incident_workflow()

    print("\n" + "=" * 80)
    print("🌐  MICROSOFT AGENT FRAMEWORK - DEVUI MULTI-AGENT WORKFLOW INSPECTOR")
    print("=" * 80)
    print(f"📡  Servidor DevUI disponible en: http://localhost:{port}")
    print("📦  Entidades registradas:")
    print(f"    - Workflow : {workflow.name}")
    print(f"    - Agente 1 : {log_analyst.name}")
    print(f"    - Agente 2 : {remediation_planner.name}")
    print("\n💡  Demostración del Flujo Completo en el Navegador:")
    print(f"  1. Abre en tu navegador: http://localhost:{port}")
    print("  2. En el menú superior o selector de entidades, elige el Workflow.")
    print("  3. Copia y envía este log de incidente:")
    print("     \"FATAL: payments-service pod crash (OOMKilled, heap memory 100%). "
          "Requests failing with 503 Service Unavailable.\"")
    print("  4. Puntos de Inspección Visual:")
    print("     a) Visualiza la transición de estado: LogAnalystAgent -> RemediationPlannerAgent.")
    print("     b) Observa la COMPUERTA HUMAN-IN-THE-LOOP:")
    print("        Cuando el agente intente invocar 'apply_cluster_remediation', DevUI pausará")
    print("        la ejecución y mostrará un botón de aprobación con los argumentos propuestos.")
    print("     c) Haz clic en 'Approve' para completar el ciclo.")
    print("  5. Abre la pestaña 'Traces / OpenTelemetry' para auditar los tiempos por nodo.")
    print("=" * 80)
    print("Presiona Ctrl+C para detener el servidor.\n")

    serve(
        entities=[workflow, log_analyst, remediation_planner],
        port=port,
        host="127.0.0.1",
        auto_open=False,
        auth_enabled=False
    )


if __name__ == "__main__":
    main()
