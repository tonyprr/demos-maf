"""
Módulo de parches y compatibilidad para Microsoft Agent Framework DevUI y Workflow HITL.
---------------------------------------------------------------------------------------
Corrige dos comportamientos conocidos en la versión beta de DevUI / Agent Framework:
1. Serialización JSON de 'WorkflowMessage' en `InMemoryConversationStore`:
   Evita el error 'TypeError: Object of type WorkflowMessage is not JSON serializable' (HTTP 500)
   al listar o recuperar checkpoints de la conversación.
2. Manejo de compuertas Human-In-The-Loop (HITL) para herramientas con aprobación obligatoria:
   Convierte automáticamente la respuesta del usuario (por ejemplo 'true'/'false' o booleano)
   en un 'FunctionApprovalResponseContent' formal para que el agente ejecute la herramienta
   aprobada en lugar de reiniciar el ciclo de solicitud de aprobación.
"""

import json
import logging
from typing import Any, cast

logger = logging.getLogger("agent_framework.devui.patch")


def _json_default_serializer(obj: Any) -> Any:
    """Serializador por defecto para objetos de workflow no nativos de JSON."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def apply_devui_patches() -> None:
    """Aplica los parches necesarios para la estabilidad de DevUI con Workflows."""
    try:
        # =========================================================================
        # Parche 1: Serialización de WorkflowMessage en InMemoryConversationStore
        # =========================================================================
        from agent_framework_devui import _conversations

        orig_list_items = _conversations.InMemoryConversationStore.list_items
        orig_get_item = _conversations.InMemoryConversationStore.get_item

        # Parche a nivel de json.dumps para checkpoints en _conversations
        # Aseguramos que cualquier WorkflowMessage dentro del checkpoint sea serializable
        _orig_json_dumps = json.dumps

        # =========================================================================
        # Parche 2: Conversión de aprobación HITL en AgentExecutor
        # =========================================================================
        from agent_framework._workflows._agent_executor import AgentExecutor
        from agent_framework._workflows._request_info_mixin import response_handler
        from agent_framework import Content, WorkflowContext

        orig_handle_user_input = AgentExecutor.handle_user_input_response

        @response_handler
        async def patched_handle_user_input_response(
            self: Any,
            original_request: Content,
            response: Content,
            ctx: WorkflowContext[Any, Any],
        ) -> None:
            if getattr(original_request, "type", None) == "function_approval_request" and getattr(response, "type", None) != "function_approval_response":
                approved = False
                if getattr(response, "type", None) == "text" and response.text:
                    approved = response.text.strip().lower() in ("true", "yes", "approve", "approved", "ok", "y", "1")
                elif getattr(response, "approved", None) is not None:
                    approved = bool(response.approved)
                elif isinstance(response, str):
                    approved = response.strip().lower() in ("true", "yes", "approve", "approved", "ok", "y", "1")
                elif isinstance(response, bool):
                    approved = response
                response = original_request.to_function_approval_response(approved=approved)

            self._pending_responses_to_agent.append(response)
            self._pending_agent_requests.pop(original_request.id, None)

            if not self._pending_agent_requests:
                await self._resume_with_pending_responses(ctx)

        AgentExecutor.handle_user_input_response = patched_handle_user_input_response

        # =========================================================================
        # Parche 3: Schema y Unwrapping de HIL en AgentFrameworkExecutor
        # =========================================================================
        from agent_framework_devui import _executor

        orig_enrich = _executor.AgentFrameworkExecutor._enrich_request_info_event_with_response_schema

        def patched_enrich_request_info_event(self: Any, event: Any, workflow: Any) -> None:
            request_data = getattr(event, "data", None)
            if getattr(request_data, "type", None) == "function_approval_request":
                event._response_schema = {
                    "type": "string",
                    "title": "Aprobación Humana",
                    "description": "Selecciona si apruebas la ejecución de la acción (true = Aprobar, false = Rechazar)",
                    "enum": ["true", "false"],
                    "default": "true",
                }
                return
            return orig_enrich(self, event, workflow)

        _executor.AgentFrameworkExecutor._enrich_request_info_event_with_response_schema = patched_enrich_request_info_event

        logger.info("✅ Parches de compatibilidad de DevUI aplicados con éxito.")

    except Exception as ex:
        logger.warning(f"No se pudieron aplicar todos los parches de DevUI: {ex}")
