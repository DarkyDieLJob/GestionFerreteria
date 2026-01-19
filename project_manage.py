#!/usr/bin/env python3
import argparse
import os
import shlex
import subprocess
import sys
from typing import List


def run(cmd: List[str], tolerate=False) -> int:
    print(f"\n$ {' '.join(shlex.quote(c) for c in cmd)}")
    try:
        proc = subprocess.run(cmd, check=not tolerate)
        return proc.returncode
    except subprocess.CalledProcessError as e:
        if tolerate:
            print(f"[skip] comando falló pero se tolera: {e}")
            return e.returncode
        raise


def compose_cmd() -> List[str]:
    return ["docker", "compose"]


def add_common_args(p: argparse.ArgumentParser):
    p.add_argument("--profile", dest="profiles", help="Perfiles separados por coma (db,broker,worker,frontend)")
    p.add_argument("--services", help="Servicios separados por coma (app,db,worker)")


def parse_profiles(args) -> List[str]:
    value = args.profiles or os.environ.get("PROFILE") or os.environ.get("PROFILES")
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def parse_services(args) -> List[str]:
    value = args.services or os.environ.get("SERVICES")
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def cmd_up(args):
    cmd = compose_cmd() + ["up", "-d"]
    if args.build or os.environ.get("BUILD") == "1":
        cmd.append("--build")
    for p in parse_profiles(args):
        cmd += ["--profile", p]
    return run(cmd, tolerate=True)


def cmd_down(args):
    cmd = compose_cmd() + ["down"]
    if args.volumes:
        cmd.append("--volumes")
    if args.remove_orphans:
        cmd.append("--remove-orphans")
    return run(cmd, tolerate=True)


def cmd_restart(args):
    cmd = compose_cmd() + ["restart"]
    services = parse_services(args)
    if services:
        cmd += services
    return run(cmd, tolerate=True)


def cmd_rebuild(args):
    cmd = compose_cmd() + ["build"]
    if args.no_cache:
        cmd.append("--no-cache")
    if args.pull:
        cmd.append("--pull")
    for p in parse_profiles(args):
        cmd += ["--profile", p]
    return run(cmd, tolerate=True)


def cmd_logs(args):
    cmd = compose_cmd() + ["logs"]
    if args.follow or os.environ.get("FOLLOW") == "1":
        cmd.append("-f")
    if args.since:
        cmd += ["--since", args.since]
    if args.tail:
        cmd += ["--tail", str(args.tail)]
    services = parse_services(args)
    if services:
        cmd += services
    return run(cmd, tolerate=True)


def cmd_migrate(args):
    # makemigrations (opcional, por defecto false)
    if args.makemigrations:
        run(compose_cmd() + ["run", "--rm", "app", "python", "src/manage.py", "makemigrations", "--noinput"], tolerate=True)
    # migrate (siempre)
    return run(compose_cmd() + ["run", "--rm", "app", "python", "src/manage.py", "migrate", "--noinput"], tolerate=False)


def cmd_status(_args):
    return run(compose_cmd() + ["ps"], tolerate=True)


def cmd_trigger(args):
    # Verificar si worker/broker existen; si no, avisar y salir sin error
    rc_worker = run(compose_cmd() + ["ps", "worker"], tolerate=True)
    rc_broker = run(compose_cmd() + ["ps", "redis"], tolerate=True)
    if rc_worker != 0 or rc_broker != 0:
        print("[skip] worker/broker no activos o no definidos; trigger omitido.")
        return 0
    task = args.task
    task_args = args.args or "{}"
    return run(compose_cmd() + [
        "exec", "-T", "worker", "python", "src/manage.py", "shell", "-c",
        f"from celery import current_app as app; import json; app.send_task('{task}', kwargs=json.loads('''{task_args}'''))"
    ], tolerate=True)


def cmd_compose(args):
    # Passthrough: todo lo que sigue a -- se envía tal cual a docker compose
    if not args.passthrough:
        print("Nada para pasar a docker compose. Usa: project_manage.py compose -- <args>")
        return 1
    return run(compose_cmd() + args.passthrough, tolerate=True)


def cmd_info(_args):
    print("Proyecto:", os.path.basename(os.getcwd()))
    print("Rama (si aplica):", os.environ.get("GIT_BRANCH", "(no detectada)"))
    print("Perfiles (PROFILE/PROFILES):", os.environ.get("PROFILE") or os.environ.get("PROFILES") or "(no definidos)")
    print("Servicios (SERVICES):", os.environ.get("SERVICES") or "(no definidos)")
    print("Flags entrypoint relevantes:")
    print("  NO_FRONTEND=", os.environ.get("NO_FRONTEND"))
    print("  ENABLE_COLLECTSTATIC=", os.environ.get("ENABLE_COLLECTSTATIC"))
    print("  RUN_MAKEMIGRATIONS=", os.environ.get("RUN_MAKEMIGRATIONS"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="project_manage.py", description="CLI de gestión para DjangoProyects")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("up", help="Levanta servicios (docker compose up -d)")
    add_common_args(sp)
    sp.add_argument("--build", action="store_true", help="Forzar build al levantar")
    sp.set_defaults(func=cmd_up)

    sp = sub.add_parser("down", help="Detiene y elimina servicios (docker compose down)")
    sp.add_argument("--volumes", action="store_true", help="Elimina volúmenes")
    sp.add_argument("--remove-orphans", action="store_true", help="Elimina huérfanos")
    sp.set_defaults(func=cmd_down)

    sp = sub.add_parser("restart", help="Reinicia servicios (docker compose restart)")
    add_common_args(sp)
    sp.set_defaults(func=cmd_restart)

    sp = sub.add_parser("rebuild", help="Reconstruye imágenes (docker compose build)")
    add_common_args(sp)
    sp.add_argument("--no-cache", action="store_true")
    sp.add_argument("--pull", action="store_true")
    sp.set_defaults(func=cmd_rebuild)

    sp = sub.add_parser("logs", help="Logs de servicios (docker compose logs)")
    add_common_args(sp)
    sp.add_argument("-f", "--follow", action="store_true")
    sp.add_argument("--since", help="Tiempo relativo/absoluto, ej: 2m, 2024-01-01T00:00")
    sp.add_argument("--tail", type=int, help="Cantidad de líneas por servicio")
    sp.set_defaults(func=cmd_logs)

    sp = sub.add_parser("migrate", help="Ejecuta migraciones controladas")
    sp.add_argument("--makemigrations", action="store_true", help="Ejecutar makemigrations antes de migrate")
    sp.set_defaults(func=cmd_migrate)

    sp = sub.add_parser("status", help="Estado de servicios (docker compose ps)")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("trigger", help="Dispara una tarea Celery (si worker/broker activos)")
    sp.add_argument("--task", required=True, help="Ruta de la tarea, ej: core_app.tasks.rebuild_cache")
    sp.add_argument("--args", help="JSON de kwargs para la tarea")
    sp.set_defaults(func=cmd_trigger)

    sp = sub.add_parser("compose", help="Passthrough a docker compose: project_manage.py compose -- <args>")
    sp.add_argument("passthrough", nargs=argparse.REMAINDER)
    sp.set_defaults(func=cmd_compose)

    sp = sub.add_parser("info", help="Información de contexto del proyecto")
    sp.set_defaults(func=cmd_info)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
