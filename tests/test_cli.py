"""CLI sessions through the real ``branch_queue.py`` entry point."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "branch_queue.py"


def run_cli(args: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.run(
        [sys.executable, str(PROGRAM), *args],
        input=stdin,
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=ROOT,
        timeout=10,
        check=False,
        env=env,
    )


def feed(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def test_cli_session_groups_calls_and_survives_invalid_input():
    proc = run_cli(
        ["--lang", "es"],
        feed(
            [
                "1",
                "Ana Ruiz",
                "deposit",
                "1",
                "Bea Sol",
                "withdrawal",
                "1",
                "Carlos Méndez",
                "deposito",
                "3",
                "4",
                "2",
                "deposit",
                "5",
                "deposit",
                "2",
                "withdrawal",
                "2",
                "withdrawal",
                "2",
                "not-a-service",
                "1",
                "",
                "6",
                "99",
                "3",
                "0",
            ]
        ),
    )
    output = proc.stdout
    assert proc.returncode == 0
    assert "Traceback" not in output
    assert "Traceback" not in proc.stderr
    assert proc.stderr == ""

    assert "Opción: 1\nNombre del cliente: Ana Ruiz\n" in output
    assert "Servicio: deposito\n" in output
    assert output.count("Ticket emitido") == 3
    assert output.count("Cliente llamado") == 2
    assert "es el siguiente en ser llamado" in output
    assert "hay 1 delante" in output
    assert "Sigue en la cola." in output
    assert "Ya no está en la cola." in output
    assert "No hay clientes esperando para Retiros (withdrawal)." in output
    assert "Tipo de servicio no válido: 'not-a-service'." in output
    assert "El nombre del cliente no puede estar vacío." in output
    assert "deposito -> deposit" in output
    assert "Opción no reconocida: '99'." in output
    assert "Sesión terminada. Los tickets solo existían en memoria." in output
    assert "deposit (Depósitos)" in output
    assert "  total" in output

    lists = output.split("Lista de espera")
    assert len(lists) == 3
    last_list = lists[-1]
    deposit, withdrawal = last_list.split("Retiros (withdrawal)")
    assert "#3" in deposit
    assert "Carlos Méndez" in deposit
    assert "#1" not in last_list
    assert "#2" not in last_list
    assert "(nadie en espera)" not in deposit
    assert "(nadie en espera)" in withdrawal


def test_cli_empty_list_states_the_next_action():
    proc = run_cli(["--lang", "es"], feed(["3", "0"]))
    assert proc.returncode == 0
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "(nadie en espera)" in proc.stdout
    assert "Total en espera: 0" in proc.stdout
    assert "Siguiente paso: opción 1 para emitir un ticket." in proc.stdout


def test_cli_english_empty_invalid_and_exit():
    proc = run_cli(
        ["--lang", "en"],
        feed(
            [
                "3",
                "1",
                "Ann Cole",
                "account_management",
                "2",
                "account_management",
                "2",
                "account_management",
                "1",
                "Bob",
                "loan",
                "0",
            ]
        ),
    )
    output = proc.stdout
    assert proc.returncode == 0
    assert "Traceback" not in output + proc.stderr
    assert "Next step: choose 1 to issue a ticket." in output
    assert "Ticket issued" in output
    assert "Ann Cole" in output
    assert "Client called" in output
    assert "Removed from the queue." in output
    assert "No clients are waiting for Account management (account_management)." in output
    assert "Invalid service type: 'loan'." in output
    assert "Session ended. Tickets existed only in memory." in output


def test_cli_switches_language_and_eof_does_not_crash():
    switched = run_cli(["--lang", "es"], feed(["7", "0"]))
    assert switched.returncode == 0
    assert "Emitir ticket" in switched.stdout
    assert "Issue a ticket" in switched.stdout
    assert "Session ended. Tickets existed only in memory." in switched.stdout
    assert "Traceback" not in switched.stdout + switched.stderr

    ended = run_cli(["--lang", "es"], "")
    assert ended.returncode == 0
    assert "Fin de la entrada. Sesión terminada sin guardar." in ended.stdout
    assert "Traceback" not in ended.stdout + ended.stderr


def test_cli_rejects_unknown_language_without_a_traceback():
    proc = run_cli(["--lang", "fr"], "")
    assert proc.returncode == 2
    assert "Traceback" not in proc.stdout + proc.stderr
    assert "invalid choice" in proc.stderr
