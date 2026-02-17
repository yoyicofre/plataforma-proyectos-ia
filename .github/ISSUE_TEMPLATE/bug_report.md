name: Bug
description: Reporte de bug
body:
  - type: textarea
    id: observed
    attributes:
      label: Observado
      description: ¿Qué ocurrió?
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Esperado
      description: ¿Qué debería ocurrir?
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Pasos para reproducir
      description: Paso a paso
    validations:
      required: true
