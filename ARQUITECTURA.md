# 🏛️ Arquitectura del Microsoft Agent Framework (MAF)

Este documento detalla la base arquitectónica y los conceptos de diseño de **Microsoft Agent Framework** y su entorno de desarrollo visual **DevUI**.

---

## 1. Contexto y Evolución del Ecosistema Microsoft

Hasta principios de 2025/2026, el ecosistema de IA generativa de Microsoft presentaba dos vertientes complementarias pero divididas:

```mermaid
graph TD
    A[AutoGen v0.2 / v0.4<br/>- Conversaciones Multi-Agente<br/>- Flexibilidad de Orquestación<br/>- Prototipado Rápido] --> C[Microsoft Agent Framework<br/><b>agent-framework</b><br/><i>Unificación Enterprise</i>]
    B[Semantic Kernel<br/>- Conectores Empresariales<br/>- Tipado Estricto C#/Python<br/>- Filtros, Middleware y OTel] --> C
    
    C --> D[DevUI<br/><b>agent-framework-devui</b><br/>Visualizador, Inspector y Playground]
    C --> E[Production Runtimes<br/>Azure Container Apps / Kubernetes / Cloud Services]
```

* **AutoGen (legado):** Excelente para dinámicas conversacionales y prototipado multi-agente, pero con dificultades para control determinista y gobierno corporativo.
* **Semantic Kernel (legado):** Excelente para integración empresarial, filtros, plugins y contratos de software, pero con abstracciones multi-agente más rígidas.
* **Microsoft Agent Framework (MAF):** La **unificación oficial y estable**. Combina el modelo de orquestación flexible de AutoGen con la robustez arquitectónica, tipado estricto, observabilidad (OpenTelemetry) y middleware de Semantic Kernel.

---

## 2. Componentes Nucleares de la Arquitectura

```mermaid
classDiagram
    class Agent {
        +String name
        +String instructions
        +ChatClient client
        +List~Tool~ tools
        +Context context
        +run(prompt)
        +run_stream(prompt)
    }

    class ChatClient {
        <<interface>>
        +create_completion(messages, tools)
    }

    class Tool {
        +String name
        +String description
        +Type input_schema
        +execute(args)
    }

    class Workflow {
        +List~Node~ nodes
        +List~Edge~ transitions
        +run(initial_state)
        +pause_for_human(checkpoint)
    }

    Agent --> ChatClient : Inyecta
    Agent --> Tool : Ejecuta mediante Function Calling
    Workflow o-- Agent : Orquesta como Nodos
```

### 2.1. El Agente como Actor Dirigido por Eventos
Para un ingeniero de software tradicional, un `Agent` en MAF no es una función aislada, sino un **Actor con estado**:
1. **Receptor de Mensajes:** Acepta entradas en un buffer o cola de contexto.
2. **Bucle de Inferencia (*Reasoning Loop*):** Decide si responde directamente con texto o si invoca una o más herramientas en paralelo o secuenciales.
3. **Despacho de Herramientas (*Tool Dispatcher*):** Valida los argumentos recibidos mediante esquemas JSON generados por reflexión a partir de tipos de Python (`pydantic` o `typing`).
4. **Emisión de Eventos:** Publica eventos estructurados (`AgentRunStarted`, `ToolCallInvoked`, `ToolCallResult`, `AgentRunCompleted`) que pueden ser consumidos por observadores o por **DevUI**.

---

## 3. Ciclo de Vida del *Tool Calling* y Validación de Contratos

Uno de los mayores riesgos en aplicaciones de IA es el comportamiento no determinista de los argumentos de entrada. MAF mitiga esto forzando contratos tipados:

```mermaid
%%{init: {'themeVariables': {'noteTextColor': '#212529', 'noteBkgColor': '#e9ecef', 'noteBorderColor': '#adb5bd'}}}%%
sequenceDiagram
    autonumber
    actor Dev as Usuario / DevUI
    participant Agent as MAF Agent
    participant LLM as Modelo (OpenAI / Azure)
    participant Tool as Función / Tool Tipada

    Dev->>Agent: Prompt: "Revisa salud del servicio auth-api"
    Agent->>LLM: Mensajes + Schemas JSON de Tools registradas
    LLM-->>Agent: tool_call: check_health({ "service_name": "auth-api" })
    
    rect rgba(0, 120, 212, 0.1)
        Note over Agent,Tool: Fase de Validación de Contratos
        Agent->>Agent: Valida payload contra Pydantic Model
        alt Argumentos inválidos
            Agent-->>LLM: Error estructurado de validación (Auto-corrección)
        else Argumentos válidos
            Agent->>Tool: execute(params: QueryInput)
            Tool-->>Agent: Retorno: "Status: 3 pods unhealthy"
        end
    end

    Agent->>LLM: Tool Result ("Status: 3 pods unhealthy")
    LLM-->>Agent: Respuesta final en lenguaje natural
    Agent-->>Dev: Diagnóstico y pasos de remediación
```

---

## 4. Arquitectura de DevUI (`agent-framework-devui`)

**DevUI** actúa como un *Harness* de pruebas local sin requerir que el equipo construya un frontend React o Angular para validar los agentes.

```mermaid
graph LR
    subgraph Browser["Navegador Web (localhost:8090)"]
        UI[Playground Visual<br/>Chat / Graph Viewer]
        TraceView[Trace Inspector<br/>OpenTelemetry Viewer]
    end

    subgraph DevUIServer["DevUI Server (FastAPI / Uvicorn)"]
        SSE[SSE / WebSocket Engine<br/>Streaming de Eventos]
        Proxy[OpenAI-Compatible API<br/>/v1/chat/completions]
        Registry[Entities Registry<br/>Agents & Workflows]
    end

    subgraph CoreEngine["MAF Core Engine"]
        WF[Workflow State Machine]
        Ag[Agent Instances]
        OTel[OTel Tracing Provider]
    end

    UI <-->|HTTP / SSE| SSE
    TraceView <-->|Trazas JSON| OTel
    SSE <--> Registry
    Registry <--> WF
    Registry <--> Ag
    Proxy <--> Ag
```

### Capacidades Clave de DevUI:
1. **Descubrimiento Automático o Programático:** Registra agentes y flujos en memoria mediante `serve(entities=[...])` o escaneando un directorio.
2. **Visualización de Grafos de Trabajo:** Despliega los nodos de un `Workflow` indicando en tiempo real el nodo activo, las transiciones y los payloads transferidos.
3. **Pausa para Intervención Humana (HITL):** Cuando un flujo entra en estado de espera (*Human Approval*), la interfaz presenta un modal de confirmación con los argumentos propuestos antes de permitir que el workflow continúe.
4. **Backend Compatible con OpenAI:** Expone el endpoint `/v1/chat/completions`, lo que permite probar el agente desde herramientas estándar como `curl`, Postman o tests automatizados sin alterar el código.

---

## 5. Arquitectura del Flujo del Laboratorio 3 (Pipeline con HITL)

En [GUIA_LABORATORIOS.md](./GUIA_LABORATORIOS.md), implementamos este patrón de arquitectura empresarial:

```mermaid
flowchart TD
    In([Logs en Bruto del Incidente]) --> N1[Nodo 1: LogAnalystAgent]
    N1 --> StateCheck{Evaluación de Severidad}
    
    StateCheck -->|CRITICAL / HIGH| Gate[Nodo 2: HumanApprovalCheckpoint<br/><b>Pausa de Ejecución</b>]
    StateCheck -->|LOW / MEDIUM| N3[Nodo 3: RemediationPlannerAgent]
    
    Gate -->|Rechazado| AbortNode([Fin: Escalar a Guardia Humana])
    Gate -->|Aprobado en DevUI / Consola| N3
    
    N3 --> Out([Plan de Mitigación y Script Validado])

    classDef agentNode fill:#d1ecf1,stroke:#0c5460,stroke-width:2px,color:#0a3641;
    classDef gateNode fill:#fff3cd,stroke:#856404,stroke-width:2px,color:#533f03;
    classDef endNode fill:#d4edda,stroke:#155724,stroke-width:2px,color:#0f5132;
    classDef checkNode fill:#e9ecef,stroke:#495057,stroke-width:2px,color:#212529;
    
    class N1,N3 agentNode;
    class Gate gateNode;
    class In,Out,AbortNode endNode;
    class StateCheck checkNode;
```

### Principios de Ingeniería Aplicados:
* **Inmutabilidad y Paso de Estado:** Cada nodo recibe una instantánea del estado del incidente y retorna una copia actualizada con su resultado.
* **Idempotencia:** Las herramientas de diagnóstico son de solo lectura; las acciones de modificación están aisladas detrás del nodo de aprobación.
* **Separación de Responsabilidades:** El analizador de logs no conoce cómo remediar; el planificador de remediación no analiza logs sin procesar, solo consume el diagnóstico estructurado.
