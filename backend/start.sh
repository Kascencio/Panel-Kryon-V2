#!/bin/bash
# Script para iniciar el backend de Panel Kryon

cd "$(dirname "$0")"

# Verificar si el puerto 8000 está en uso
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Puerto 8000 en uso. Matando proceso anterior..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Activar entorno virtual y ejecutar
export PYTHONPATH="$(pwd)"
./venv/bin/python -m uvicorn app.main:app --reload --port 8000
