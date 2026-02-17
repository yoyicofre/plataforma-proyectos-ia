# Frontend Static Deploy (S3)

## Objetivo
Desplegar `frontend/dist` como sitio estatico en S3, opcionalmente con CloudFront.

## Requisitos
- AWS CLI instalado y autenticado (`aws configure` o SSO).
- Bucket S3 para hosting estatico.
- (Recomendado) CloudFront delante del bucket para HTTPS/CDN.

## Variables frontend
Define en build:
- `VITE_API_BASE_URL` (ej: `https://api.midominio.com`)

Ejemplo (PowerShell):
```powershell
$env:VITE_API_BASE_URL="https://api.midominio.com"
```

## Deploy automatizado
Script:
- `scripts/deploy_frontend_s3.ps1`

Uso:
```powershell
./scripts/deploy_frontend_s3.ps1 -BucketName my-frontend-bucket
```

Con invalidacion CloudFront:
```powershell
./scripts/deploy_frontend_s3.ps1 -BucketName my-frontend-bucket -DistributionId E123ABC456
```

## Notas
- El script ejecuta `npm install`, `npm run build` y `aws s3 sync --delete`.
- Si usas rutas SPA avanzadas, configura fallback de CloudFront/S3 a `index.html`.
