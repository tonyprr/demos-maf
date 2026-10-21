# 📁 Sesión 1: Fundamentos, Tool Calling Tipado y DevUI

En esta sesión se desarrollan los primeros 2 laboratorios prácticos de la capacitación.

---

## 🚀 Cómo Ejecutar los Laboratorios

Asegúrate de tener activado el entorno virtual (`source .venv/bin/activate` o usando `uv run`):

### 1. Lab 1: Agente Autónomo por Consola
Valida la creación del agente y la invocación de la herramienta tipada con Pydantic.
```bash
uv run python session_1/lab1_single_agent.py
# o con python tradicional:
python session_1/lab1_single_agent.py
```

### 2. Lab 2: Servidor DevUI en el Navegador
Levanta el harness local de desarrollo para inspeccionar llamadas y eventos en vivo.
```bash
uv run python session_1/lab2_devui_serve.py
# o con python tradicional:
python session_1/lab2_devui_serve.py
```
Abre en tu navegador: [http://localhost:8090](http://localhost:8090).

---

## 🎯 Puntos Clave para Ingenieros de Software
* **Contratos Fuertes (`Pydantic`):** La clase `ServiceHealthQuery` obliga al LLM a pasar tipos válidos (`service_name: str`, `environment: str`), previniendo fallos en tiempo de ejecución.
* **Separación de Responsabilidades:** El cliente de inferencia (`OpenAIChatClient`) está desacoplado de la lógica del agente y de las herramientas de consulta.
* **API OpenAI-Compatible:** DevUI provee un endpoint `/v1/chat/completions` listo para pruebas con `curl` o clientes HTTP tradicionales.
