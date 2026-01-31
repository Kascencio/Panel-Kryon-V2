#!/usr/bin/env python3
"""
Script de Migración de Terapias - Panel Kryon
=============================================

Este script importa terapias desde el USB a una instalación fresca de Panel Kryon.
Copia los archivos de audio/video y registra las terapias en la base de datos.

USO:
  1. Conecta el USB con los archivos de migración
  2. Navega a la carpeta del backend: cd backend
  3. Activa el entorno virtual: source venv/bin/activate (Linux/Mac) o venv\Scripts\activate (Windows)
  4. Ejecuta: python migrar_terapias.py --usb /ruta/al/usb

EJEMPLO WINDOWS:
  python migrar_terapias.py --usb E:\panel-kryon

EJEMPLO MAC:
  python migrar_terapias.py --usb /Volumes/USB/panel-kryon
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos de la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Migrar terapias desde USB")
    parser.add_argument("--usb", required=True, help="Ruta al directorio del USB con los archivos de migración")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría, sin ejecutar")
    args = parser.parse_args()

    usb_path = Path(args.usb)
    
    # Validar rutas
    json_path = usb_path / "migracion" / "therapies.json"
    audio_path = usb_path / "public" / "audio"
    video_path = usb_path / "public" / "videos"
    
    if not json_path.exists():
        print(f"❌ No se encontró: {json_path}")
        print("   Asegúrate de que el USB contenga la carpeta 'migracion' con therapies.json")
        sys.exit(1)
    
    print("=" * 60)
    print("   MIGRACIÓN DE TERAPIAS - PANEL KRYON")
    print("=" * 60)
    print(f"\n📂 USB: {usb_path}")
    print(f"📄 JSON: {json_path}")
    print(f"🎵 Audio: {audio_path}")
    print(f"🎬 Video: {video_path}")
    
    # Cargar terapias
    with open(json_path, "r", encoding="utf-8") as f:
        therapies = json.load(f)
    
    print(f"\n📋 Terapias encontradas: {len(therapies)}")
    
    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: No se realizarán cambios\n")
    
    # Importar módulos de la aplicación
    try:
        from app.config import settings
        from app.db import SessionLocal, engine
        from app.models import Base, Therapy
    except ImportError as e:
        print(f"\n❌ Error importando módulos de la app: {e}")
        print("   Asegúrate de ejecutar este script desde la carpeta 'backend'")
        print("   y que el entorno virtual esté activado.")
        sys.exit(1)
    
    # Directorio de media
    media_dir = Path(settings.MEDIA_DIR).resolve()
    audio_dest = media_dir / "audio"
    video_dest = media_dir / "video"
    
    print(f"\n📁 Destino media: {media_dir}")
    
    if not args.dry_run:
        audio_dest.mkdir(parents=True, exist_ok=True)
        video_dest.mkdir(parents=True, exist_ok=True)
    
    # Crear tablas si no existen
    if not args.dry_run:
        Base.metadata.create_all(bind=engine)
    
    # Procesar terapias
    session = SessionLocal()
    imported = 0
    skipped = 0
    files_copied = 0
    errors = []
    
    try:
        for t in therapies:
            therapy_id = t["id"]
            name = t["name"]
            
            # Verificar si ya existe
            existing = session.query(Therapy).filter(Therapy.name == name).first()
            if existing:
                print(f"⏭️  {name} - ya existe (ID: {existing.id})")
                skipped += 1
                continue
            
            print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}📥 Importando: {name}")
            
            # Mapear archivos de media
            audio_corto = None
            audio_mediano = None
            audio_largo = None
            video = None
            
            if "audio_files" in t:
                for dur, filename in t["audio_files"].items():
                    src = audio_path / filename
                    if src.exists():
                        dest_file = f"audio/{filename}"
                        if not args.dry_run:
                            shutil.copy2(src, audio_dest / filename)
                        print(f"   ✅ {dur}: {filename}")
                        files_copied += 1
                        
                        if dur == "corto":
                            audio_corto = dest_file
                        elif dur == "mediano":
                            audio_mediano = dest_file
                        elif dur == "largo":
                            audio_largo = dest_file
                    else:
                        print(f"   ⚠️  {dur}: {filename} - NO ENCONTRADO")
            
            if "video_files" in t:
                for dur, filename in t["video_files"].items():
                    src = video_path / filename
                    if src.exists():
                        dest_file = f"video/{filename}"
                        if not args.dry_run:
                            shutil.copy2(src, video_dest / filename)
                        print(f"   ✅ video: {filename}")
                        files_copied += 1
                        video = dest_file
                    else:
                        print(f"   ⚠️  video: {filename} - NO ENCONTRADO")
            
            # Crear registro en BD
            if not args.dry_run:
                duration_labels_json = None
                if "duration_labels" in t:
                    duration_labels_json = json.dumps(t["duration_labels"])
                
                therapy = Therapy(
                    name=name,
                    description=t.get("description", ""),
                    category=t.get("category", "session"),
                    color_mode=t.get("color_mode", "general"),
                    default_intensity=t.get("default_intensity", 50),
                    media_type=t.get("media_type", "audio"),
                    audio_corto_path=audio_corto,
                    audio_mediano_path=audio_mediano,
                    audio_largo_path=audio_largo,
                    audio_path=audio_corto,  # Legacy compatibility
                    video_path=video,
                    duration_labels=duration_labels_json,
                    is_active=True
                )
                session.add(therapy)
            
            imported += 1
        
        if not args.dry_run:
            session.commit()
        
        print("\n" + "=" * 60)
        print("   RESUMEN DE MIGRACIÓN")
        print("=" * 60)
        print(f"\n✅ Terapias importadas: {imported}")
        print(f"⏭️  Terapias omitidas (ya existían): {skipped}")
        print(f"📁 Archivos copiados: {files_copied}")
        
        if errors:
            print(f"\n❌ Errores: {len(errors)}")
            for err in errors:
                print(f"   - {err}")
        
        if args.dry_run:
            print("\n⚠️  Este fue un DRY-RUN. Ejecuta sin --dry-run para aplicar cambios.")
        else:
            print("\n🎉 ¡Migración completada exitosamente!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
