# AWS custom domains (actual)

Estado validado en `us-east-1`:

- API backend: `https://api.mktautomations.com`
- Frontend: `https://app.mktautomations.com`

Recursos actuales:

- Hosted Zone `mktautomations.com`: `Z00148751YY3Y9CNWLZLL`
- API Gateway HTTP API: `iukyi7jlw4`
- API custom domain target: `d-g103u12k74.execute-api.us-east-1.amazonaws.com`
- CloudFront distribution: `EPFK8B46IXDBC`
- CloudFront domain: `d1j5fgjzigea2f.cloudfront.net`
- Front bucket: `plataforma-ia-372665803158`

Comprobaciones rápidas:

```powershell
# Health backend
Invoke-WebRequest https://api.mktautomations.com/health -UseBasicParsing

# Frontend HTML (si tu DNS local está propagado)
Invoke-WebRequest https://app.mktautomations.com -UseBasicParsing
```

Notas:

- Si `app.mktautomations.com` no resuelve en tu red local, valida contra DNS público:

```powershell
nslookup app.mktautomations.com 8.8.8.8
```

- Frontend usa `VITE_API_BASE_URL=https://api.mktautomations.com` en `frontend/.env.local`.
