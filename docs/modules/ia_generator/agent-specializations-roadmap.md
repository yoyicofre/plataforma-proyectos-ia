# IA Generator - Agent Specializations Roadmap

Fecha: 2026-02-17  
Estado: en implementacion

## Objetivo

Definir y estandarizar los agentes especializados del modulo `Generador IA`, iniciando por `Text IA`, para que cada agente tenga:

- prompt maestro reutilizable
- contrato de entrada y salida
- proveedor/modelo recomendado
- criterios de calidad operativos

## Agente 1 (activo): Data Analyst (Economia/Contabilidad)

Codigo sugerido: `data_analyst_finance`

### Propuesta de valor

- Convierte datos y objetivos de negocio en analisis ejecutivo accionable.
- Prioriza KPIs, riesgos, hallazgos y recomendaciones concretas.

### Contexto minimo recomendado

- objetivo de negocio
- periodo analizado
- moneda
- audiencia
- nivel de detalle
- datos o notas adicionales

### Estructura de respuesta esperada

1. Resumen ejecutivo
2. KPIs clave
3. Hallazgos
4. Riesgos
5. Recomendaciones
6. Supuestos

## Catalogo inicial de especialidades Text IA

1. `data_analyst_finance`
2. `travel_planner`
3. `image_prompt_designer`
4. `video_script_strategist`

## API de especialidades

- `GET /ia/text-specialties`
  - devuelve las especialidades disponibles para frontend
  - incluye prompt maestro y recomendacion de proveedor/modelo

## Reglas operativas

1. El usuario puede usar especialidad o ejecutar modo libre.
2. Aplicar especialidad no fuerza guardado; el guardado sigue siendo explicito por iteracion.
3. Los prompts maestros deben versionarse cuando cambien criterios.
4. Toda nueva especialidad debe registrar:
   - objetivo
   - limites
   - metrica de calidad
   - riesgo principal

## Siguiente fase (proxima iteracion)

1. Prompts maestros versionados en DB (en vez de hardcode).
2. Salida estructurada JSON para `data_analyst_finance`.
3. Score de calidad por respuesta (completitud, accionabilidad, claridad).
4. Vista de comparacion A/B entre modelos para una misma consulta.
