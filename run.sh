#!/bin/bash
# Script para iniciar Panel Kryon (Backend + Frontend)

cd "$(dirname "$0")"

echo "==================================================="
echo "     INICIANDO PANEL KRYON"
echo "==================================================="

# Colores para mejor legibilidad
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ---------------------------------------------------
# 1. VERIFICAR PUERTO 8000 (Backend)
# ---------------------------------------------------
echo ""
echo -e "${BLUE}[1/3]${NC} Preparando Backend..."

if lsof -ti:8000 > /dev/null 2>&1; then
    echo "  ⚠️  Puerto 8000 en uso. Matando proceso..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# ---------------------------------------------------
# 2. VERIFICAR PUERTO 5173 (Frontend)
# ---------------------------------------------------
echo -e "${BLUE}[2/3]${NC} Preparando Frontend..."

if lsof -ti:5173 > /dev/null 2>&1; then
    echo "  ⚠️  Puerto 5173 en uso. Matando proceso..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    sleep 1
fi

# ---------------------------------------------------
# 3. INICIAR BACKEND
# ---------------------------------------------------
echo -e "${BLUE}[3/3]${NC} Iniciando servicios..."
echo ""

# Iniciar Backend en segundo plano
echo "  🚀 Backend (Puerto 8000)..."
cd backend
export PYTHONPATH="$(pwd)"
./venv/bin/python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Pequeña pausa para que el backend inicie
sleep 2

# ---------------------------------------------------
# 4. INICIAR FRONTEND
# ---------------------------------------------------
echo "  🌐 Frontend (Puerto 5173)..."
python3 -m http.server 5173 --directory external-ui &
FRONTEND_PID=$!

# ---------------------------------------------------
# 5. ABRIR NAVEGADOR
# ---------------------------------------------------
echo ""
echo "  ⏳ Esperando 3 segundos para abrir navegador..."
sleep 3

# Detectar sistema operativo y abrir navegador
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:5173/login.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "http://localhost:5173/login.html"
fi

echo ""
echo "==================================================="
echo -e "  ${GREEN}✅ PANEL KRYON INICIADO${NC}"
echo "==================================================="
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Login:    http://localhost:5173/login.html"
echo ""
echo "  Presiona Ctrl+C para detener ambos servicios"
echo ""

# Manejar Ctrl+C para matar ambos procesos
trap "echo ''; echo 'Deteniendo servicios...'; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Mantener el script corriendo
wait
