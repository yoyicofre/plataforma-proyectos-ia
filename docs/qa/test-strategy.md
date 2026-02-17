# Test Strategy

## Pirámide
- Unit: reglas de negocio en `service.py`.
- Integración: endpoints + dependencias + (DB si aplica).
- E2E: flujos críticos (si aplica).

## Criterios mínimos
- PR mergeable solo con CI verde.
- Todo bugfix debe incluir **test de regresión**.

## Datos de prueba
- Preferir fixtures claras y deterministas.
- Evitar dependencias externas en tests (mockear integraciones).
