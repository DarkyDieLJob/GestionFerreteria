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
  [switch]$SkipMigrate = $false,
  [string]$Requirements = 'notebook',
  [switch]$NoFrontend = $false,
  [switch]$ActivateShell = $false,
  [switch]$RunServer = $false
)

$ErrorActionPreference = 'Stop'

function Write-Stage($msg) {
  Write-Host "`n==> $msg" -ForegroundColor Cyan
}

# 1) Resolver Python
Write-Stage "Verificando Python"
$python = "$Env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
if (-not (Test-Path $python)) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($null -ne $cmd) { $python = $cmd.Source }
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

# 4) Instalar dependencias base (según selección)
Write-Stage "Seleccionando requirements: $Requirements"
$reqDir = Join-Path (Get-Location) "requirements"
switch -Regex ($Requirements) {
  '^(?i)dev$'        { $reqBase = Join-Path $reqDir 'dev.txt' ; break }
  '^(?i)notebook$'   { $reqBase = Join-Path $reqDir 'notebook.txt' ; break }
  '^(?i)lista(_)?v3$'{ $reqBase = Join-Path $reqDir 'lista_v3.txt' ; break }
  default            {
    # permitir ruta personalizada
    if (Test-Path $Requirements) { $reqBase = (Resolve-Path $Requirements).Path }
    else { throw "No se reconoce el requirements '$Requirements'. Use 'dev', 'notebook', 'lista_v3' o una ruta válida." }
  }
}
Write-Stage "Instalando dependencias base ($reqBase)"
& $venvPython -m pip install -r $reqBase
if ($LASTEXITCODE -ne 0) {
  throw "Fallo instalando dependencias base desde $reqBase. Revisa el archivo y tu versión de Python."
}

# 5) Paquetes requeridos no listados explícitamente en lista_v3.txt
Write-Stage "Asegurando paquetes requeridos (djangorestframework, python-decouple, django-allauth)"
& $venvPython -m pip install djangorestframework python-decouple django-allauth
if ($LASTEXITCODE -ne 0) {
  throw "Fallo asegurando paquetes requeridos."
}

# 6) Dependencias de desarrollo (opcional)
if ($Dev) {
  Write-Stage "Instalando dependencias de desarrollo (requirements/dev.txt)"
  $reqDev = Join-Path (Get-Location) "requirements/dev.txt"
  if (Test-Path $reqDev) {
    & $venvPython -m pip install -r $reqDev
    if ($LASTEXITCODE -ne 0) {
      throw "Fallo instalando dependencias de desarrollo desde $reqDev."
    }
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

# 7.1) Frontend (Tailwind) por defecto a menos que se desactive
if (-not $NoFrontend) {
  Write-Stage "Configurando frontend con Tailwind"
  $frontendDir = Join-Path (Get-Location) 'frontend'
  if (-not (Test-Path $frontendDir)) { New-Item -ItemType Directory -Path $frontendDir | Out-Null }
  if (-not (Test-Path (Join-Path $frontendDir 'src'))) { New-Item -ItemType Directory -Path (Join-Path $frontendDir 'src') | Out-Null }

  $pkgPath = Join-Path $frontendDir 'package.json'
  if (-not (Test-Path $pkgPath)) {
    @"
{
  "name": "django-frontend",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css -w",
    "build": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.10"
  }
}
"@ | Set-Content -Encoding UTF8 $pkgPath
  }

  $tailwindCfg = Join-Path $frontendDir 'tailwind.config.js'
  if (-not (Test-Path $tailwindCfg)) {
    @"
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/**/*.html",
    "../src/**/templates/**/*.html",
    "../templates/**/*.html"
  ],
  theme: { extend: {} },
  plugins: [],
};
"@ | Set-Content -Encoding UTF8 $tailwindCfg
  }

  $postcssCfg = Join-Path $frontendDir 'postcss.config.js'
  if (-not (Test-Path $postcssCfg)) {
    @"
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"@ | Set-Content -Encoding UTF8 $postcssCfg
  }

  $inputCss = Join-Path $frontendDir 'src/input.css'
  if (-not (Test-Path $inputCss)) {
    @"
@tailwind base;
@tailwind components;
@tailwind utilities;
"@ | Set-Content -Encoding UTF8 $inputCss
  }

  $staticCssDir = Join-Path (Get-Location) 'static/css'
  if (-not (Test-Path $staticCssDir)) { New-Item -ItemType Directory -Path $staticCssDir -Force | Out-Null }

  # Intentar npm install y build (si npm está disponible)
  $npm = (Get-Command npm -ErrorAction SilentlyContinue)
  if ($null -ne $npm) {
    Write-Stage "Instalando dependencias npm"
    Push-Location $frontendDir
    try {
      npm install
      Write-Stage "Construyendo CSS con Tailwind"
      npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify
    } finally {
      Pop-Location
    }
  } else {
    Write-Host "npm no encontrado. Ejecuta 'npm install' y 'npm run build' dentro de frontend/ cuando tengas Node.js." -ForegroundColor Yellow
  }
}

# 8) Migraciones
if (-not $SkipMigrate) {
  Write-Stage "Ejecutando migraciones"
  # Asegurar carpeta de base de datos SQLite
  $srcData = Join-Path (Get-Location) 'src/data'
  if (-not (Test-Path $srcData)) { New-Item -ItemType Directory -Path $srcData -Force | Out-Null }
  # Crear migraciones antes de aplicar
  & $venvPython .\src\manage.py makemigrations
  & $venvPython .\src\manage.py migrate
}

# 9) Tests (opcional)
if ($Test) {
  Write-Stage "Ejecutando tests (pytest)"
  try {
    & $venvPython -m pytest -q .\src
    $pytestExit = $LASTEXITCODE
  } catch {
    Write-Host "Pytest no disponible o falló. Instala con -Dev para incluirlo." -ForegroundColor Yellow
  }
}

if ($ActivateShell) {
  Write-Stage "Abriendo nueva PowerShell con entorno activado en src/"
  $activateCmd = ".\\venv\\Scripts\\Activate.ps1; Set-Location src"
  Start-Process powershell -ArgumentList @('-NoExit','-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-Command', $activateCmd)
}

# 10) Lanzar servidor opcionalmente
if ($RunServer) {
  $canRun = $true
  if ($Test -and ($pytestExit -ne $null) -and ($pytestExit -ne 0)) {
    $canRun = $false
    Write-Host "Tests fallaron (exitcode=$pytestExit). No se iniciará el servidor por -RunServer." -ForegroundColor Yellow
  }
  if ($canRun) {
    Write-Stage "Iniciando servidor de desarrollo"
    & $venvPython .\src\manage.py runserver
  }
}

Write-Host "`nSetup completado. Para ejecutar el servidor manualmente:" -ForegroundColor Green
Write-Host ".\venv\Scripts\python .\src\manage.py runserver" -ForegroundColor Green
Write-Host "Para activar el entorno en esta sesión: .\\venv\\Scripts\\Activate.ps1" -ForegroundColor Green
