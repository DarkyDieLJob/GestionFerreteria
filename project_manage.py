#!/usr/bin/env python3
"""
Utilidad de gestión del proyecto (atajos para Docker Compose y Celery).

Ejemplos rápidos:
- Reconstruir app y worker:
  python project_manage.py rebuild
- Reiniciar app y worker (sin rebuild):
  python project_manage.py restart
- Logs del worker (seguimiento):
  python project_manage.py logs worker -f
- Encolar procesamiento inmediato de pendientes:
  python project_manage.py trigger
- Ver tareas programadas:
  python project_manage.py status scheduled
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


def cmd_rebuild(args: argparse.Namespace) -> int:
    services = args.services or ["app", "worker"]
    return run(["docker", "compose", "up", "-d", "--no-deps", "--build", *services])


def cmd_restart(args: argparse.Namespace) -> int:
    services = args.services or ["app", "worker"]
    return run(["docker", "compose", "restart", *services])


def cmd_up(args: argparse.Namespace) -> int:
    services = args.services or []
    return run(["docker", "compose", "up", "-d", *services])


def cmd_down(args: argparse.Namespace) -> int:
    return run(["docker", "compose", "down"])


def cmd_logs(args: argparse.Namespace) -> int:
    if not args.service:
        print("Debe indicar un servicio (p.ej. app o worker)")
        return 2
    cmd = ["docker", "compose", "logs"]
    if args.follow:
        cmd.append("-f")
    cmd.append(args.service)
    return run(cmd)


def cmd_trigger(args: argparse.Namespace) -> int:
    # Encola la tarea inmediata desde el contenedor web
    py = (
        "from importaciones.tasks import procesar_pendientes_task; "
        "r = procesar_pendientes_task.apply_async(countdown=0); "
        "print(r.id)"
    )
    return run(["docker", "compose", "exec", "app", "python", "-c", py])


def cmd_status(args: argparse.Namespace) -> int:
    section = args.section.lower()
    if section not in {"active", "reserved", "scheduled"}:
        print("Sección inválida. Use: active | reserved | scheduled")
        return 2
    return run(["docker", "compose", "exec", "worker", "celery", "-A", "core_config", "inspect", section])


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Atajos para gestionar el proyecto (Docker Compose y Celery)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("rebuild", help="Reconstruir imágenes y recrear servicios (por defecto: app, worker)")
    sp.add_argument("services", nargs="*", help="Servicios a reconstruir")
    sp.set_defaults(func=cmd_rebuild)

    sp = sub.add_parser("restart", help="Reiniciar servicios sin reconstruir (por defecto: app, worker)")
    sp.add_argument("services", nargs="*", help="Servicios a reiniciar")
    sp.set_defaults(func=cmd_restart)

    sp = sub.add_parser("up", help="Levantar servicios en segundo plano (por defecto todos del compose)")
    sp.add_argument("services", nargs="*", help="Servicios a levantar")
    sp.set_defaults(func=cmd_up)

    sp = sub.add_parser("down", help="Detener y remover contenedores")
    sp.set_defaults(func=cmd_down)

    sp = sub.add_parser("logs", help="Ver logs de un servicio")
    sp.add_argument("service", help="Servicio (p.ej. app, worker, db, redis)")
    sp.add_argument("-f", "--follow", action="store_true", help="Seguir logs")
    sp.set_defaults(func=cmd_logs)

    sp = sub.add_parser("trigger", help="Encolar procesamiento inmediato de pendientes")
    sp.set_defaults(func=cmd_trigger)

    sp = sub.add_parser("status", help="Consultar estado de Celery (active/reserved/scheduled)")
    sp.add_argument("section", choices=["active", "reserved", "scheduled"], help="Sección a consultar")
    sp.set_defaults(func=cmd_status)

    return p


def main(argv: list[str]) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
