# 📁 Sesión 2: Orquestación Multi-Agente, Workflows y DevUI

En esta sesión se desarrollan los laboratorios 3 y 4 orientados a sistemas multi-agente deterministas y gobernanza de ejecución.

---

## 🚀 Cómo Ejecutar los Laboratorios

Asegúrate de tener el entorno virtual activo:

### 1. Lab 3: Pipeline Secuencial con HITL (Consola)
Construye y prueba la orquestación del pipeline `LogAnalystAgent` $\rightarrow$ `RemediationPlannerAgent` y valida la herramienta con aprobación obligatoria.
```bash
uv run python session_2/lab3_workflow.py
# o con python tradicional:
python session_2/lab3_workflow.py
```

### 2. Lab 4: Visualización de Workflow y Checkpoints en DevUI
Monta el grafo completo en DevUI para inspeccionar visualmente los nodos, la compuerta humana interactiva y las trazas OTel.
```bash
uv run python session_2/lab4_multiagent_devui.py
# o con python tradicional:
python session_2/lab4_multiagent_devui.py
```
Abre en tu navegador: [http://localhost:8090](http://localhost:8090).

---

## 🎯 Puntos Clave para Ingenieros de Software
* **Composición desacoplada (`WorkflowBuilder`):** Cada agente tiene un rol único y acotado, minimizando errores de razonamiento.
* **Human-in-the-Loop (`approval_mode="always_require"`):** Seguridad en acciones críticas de infraestructura; el agente propone la acción pero el humano conserva el control de ejecución.
* **Trazabilidad Abierta (OpenTelemetry):** Cada salto del grafo genera spans exportables hacia herramientas como Azure Monitor, Datadog o Jaeger.
