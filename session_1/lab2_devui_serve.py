"""
Lab 2: Montaje y Depuración en DevUI (Microsoft Agent Framework)
--------------------------------------------------------------
Objetivo:
  - Exponer el agente SRE construido en el Lab 1 en la interfaz visual DevUI.
  - Inspeccionar el flujo de llamadas a herramientas (payloads JSON y respuestas).
  - Validar el endpoint compatible con la API de OpenAI (/v1/chat/completions).
"""
import os
import sys
from dotenv import load_dotenv

# Importar serve de devui y el agente del Lab 1
from agent_framework.devui import serve

# Añadir el directorio actual al path para importar el Lab 1 limpiamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lab1_single_agent import create_sre_agent

load_dotenv()


def main():
    port = int(os.getenv("DEVUI_PORT", "8090"))
    agent = create_sre_agent()

    print("\n" + "=" * 75)
    print("🚀  MICROSOFT AGENT FRAMEWORK - DEVUI SERVER")
    print("=" * 75)
    print(f"📡  Servidor DevUI disponible en: http://localhost:{port}")
    print(f"🤖  Agente registrado: {agent.name}")
    print("\n💡  Guía para la Demostración en Vivo:")
    print(f"  1. Abre en tu navegador: http://localhost:{port}")
    print("  2. En el panel de agentes selecciona 'SREDiagnosticAgent'.")
    print("  3. Envía una consulta técnica:")
    print("     -> 'Revisa el estado de auth-service en producción'")
    print("     -> Observa en el panel derecho el JSON de entrada y salida de la Tool.")
    print("  4. Envía una consulta no relacionada (fuera de dominio):")
    print("     -> '¿Cómo preparo una lasagna vegetariana?'")
    print("     -> Observa cómo el agente no alucina herramientas y declina con educación.")
    print("\n🧪  Prueba alternativa mediante curl (API compatible con OpenAI):")
    print(f"  curl -X POST http://localhost:{port}/v1/chat/completions \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"messages\": [{\"role\": \"user\", \"content\": \"Estado de payments-api en staging\"}]}'")
    print("=" * 75)
    print("Presiona Ctrl+C en cualquier momento para detener el servidor.\n")

    # auth_enabled=False permite interacción directa en el taller sin token de sesión local
    serve(
        entities=[agent],
        port=port,
        host="127.0.0.1",
        auto_open=False,
        auth_enabled=False
    )


if __name__ == "__main__":
    main()
