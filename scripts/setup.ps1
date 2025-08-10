<#
.SYNOPSIS
  Setup del proyecto en Windows (PowerShell)

.DESCRIPTION
  Crea y activa venv, instala dependencias, genera .env (si falta), ejecuta migraciones
  y opcionalmente instala dependencias de desarrollo y corre tests.

.PARAMETER Dev
  Instala dependencias de desarrollo (requirements/dev.txt)

.PARAMETER Test
  Ejecuta la suite de tests con pytest al finalizar las migraciones

.PARAMETER SkipMigrate
  Omite la ejecución de migraciones

.NOTES
  Ejecutar desde la raíz del repo.
  Ejemplos:
    pwsh -File .\scripts\setup.ps1 -Dev -Test
    powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#>

param(
  [switch]$Dev = $false,
  [switch]$Test = $false,
  [switch]$SkipMigrate = $false
)

$ErrorActionPreference = 'Stop'

function Write-Stage($msg) {
  Write-Host "`n==> $msg" -ForegroundColor Cyan
}

# 1) Resolver Python
Write-Stage "Verificando Python"
$python = "$Env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
if (-not (Test-Path $python)) {
  $python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
}
if (-not $python) {
  throw "Python no encontrado. Instala Python 3.10+ y vuelve a intentar."
}
Write-Host "Usando Python: $python"

# 2) Crear venv
Write-Stage "Creando entorno virtual (venv)"
if (-not (Test-Path "venv")) {
  & $python -m venv venv
}

$venvPython = Join-Path (Resolve-Path "venv").Path "Scripts/python.exe"
if (-not (Test-Path $venvPython)) { throw "No se encontró python en venv: $venvPython" }

# 3) Actualizar pip
Write-Stage "Actualizando pip"
& $venvPython -m pip install --upgrade pip

# 4) Instalar dependencias base
Write-Stage "Instalando dependencias base (requirements/lista_v3.txt)"
$reqBase = Join-Path (Get-Location) "requirements/lista_v3.txt"
if (-not (Test-Path $reqBase)) { throw "No existe $reqBase" }
& $venvPython -m pip install -r $reqBase

# 5) Paquetes requeridos no listados explícitamente en lista_v3.txt
Write-Stage "Asegurando paquetes requeridos (djangorestframework, python-decouple)"
& $venvPython -m pip install djangorestframework python-decouple

# 6) Dependencias de desarrollo (opcional)
if ($Dev) {
  Write-Stage "Instalando dependencias de desarrollo (requirements/dev.txt)"
  $reqDev = Join-Path (Get-Location) "requirements/dev.txt"
  if (Test-Path $reqDev) {
    & $venvPython -m pip install -r $reqDev
  } else {
    Write-Host "No se encontró requirements/dev.txt, se omite." -ForegroundColor Yellow
  }
}

# 7) .env
Write-Stage "Preparando archivo de entorno src/.env"
$envExample = Join-Path (Get-Location) "src/.env.example"
$envPath = Join-Path (Get-Location) "src/.env"
if (-not (Test-Path $envPath)) {
  if (Test-Path $envExample) {
    Copy-Item $envExample $envPath
    Write-Host "Creado src/.env desde src/.env.example"
  } else {
    @"
SECRET_KEY=changeme_super_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

NOMBRE_APLICACION=DjangoProyects
WHATSAPP_CONTACT=+00 000 000 000
PASSWORD_RESET_TICKET_TTL_HOURS=48
TEMP_PASSWORD_LENGTH=16

GITHUB_CLIENT_ID=
GITHUB_SECRET=
"@ | Set-Content -Encoding UTF8 $envPath
    Write-Host "Creado src/.env por defecto"
  }
} else {
  Write-Host "src/.env ya existe, no se modifica." -ForegroundColor Yellow
}

# 8) Migraciones
if (-not $SkipMigrate) {
  Write-Stage "Ejecutando migraciones"
  & $venvPython .\src\manage.py migrate
}

# 9) Tests (opcional)
if ($Test) {
  Write-Stage "Ejecutando tests (pytest)"
  try {
    & $venvPython -m pytest -q .\src
  } catch {
    Write-Host "Pytest no disponible o falló. Instala con -Dev para incluirlo." -ForegroundColor Yellow
  }
}

Write-Host "`nSetup completado. Para ejecutar el servidor:" -ForegroundColor Green
Write-Host ".\venv\Scripts\python .\src\manage.py runserver" -ForegroundColor Green
