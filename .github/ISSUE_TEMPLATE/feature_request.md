name: Feature
description: Nueva funcionalidad
body:
  - type: textarea
    id: problem
    attributes:
      label: Problema
      description: ¿Qué problema se resuelve?
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Propuesta
      description: ¿Qué se propone construir?
    validations:
      required: true
  - type: textarea
    id: ac
    attributes:
      label: Criterios de aceptación
      description: Lista de AC verificables.
    validations:
      required: true
