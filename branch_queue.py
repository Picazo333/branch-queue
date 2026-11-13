#!/usr/bin/env python3
"""Tagged service queue for a bank-branch terminal.

Entry point: ``python3 branch_queue.py``.

Each service type has its own ``collections.deque``. Ticket numbers come
from one global counter. Design notes: DESIGN.md.
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

SERVICE_TYPES: tuple[str, ...] = (
    "deposit",
    "withdrawal",
    "account_management",
)

# README.es.md names. Stored tickets always use the English canonical id.
SPANISH_ALIASES: dict[str, str] = {
    "deposit": "deposito",
    "withdrawal": "retiro",
    "account_management": "gestion_cuenta",
}

_ALIAS_TO_CANONICAL: dict[str, str] = {service: service for service in SERVICE_TYPES}
_ALIAS_TO_CANONICAL.update(
    {alias: canonical for canonical, alias in SPANISH_ALIASES.items()}
)

LABELS: dict[str, dict[str, str]] = {
    "es": {
        "deposit": "Depósitos",
        "withdrawal": "Retiros",
        "account_management": "Gestión de cuenta",
    },
    "en": {
        "deposit": "Deposits",
        "withdrawal": "Withdrawals",
        "account_management": "Account management",
    },
}

_MENU: tuple[tuple[str, dict[str, str]], ...] = (
    ("1", {"es": "Emitir ticket", "en": "Issue a ticket"}),
    ("2", {"es": "Llamar al siguiente cliente", "en": "Call the next client"}),
    ("3", {"es": "Ver la lista de espera", "en": "Show the waiting list"}),
    ("4", {"es": "Ver estadísticas", "en": "Show statistics"}),
    ("5", {"es": "Ver el siguiente sin retirarlo", "en": "Show the next client without removing them"}),
    ("6", {"es": "Ayuda", "en": "Help"}),
    ("7", {"es": "Cambiar idioma (ahora: español)", "en": "Switch language (now: English)"}),
    ("0", {"es": "Salir", "en": "Exit"}),
)


class QueueError(Exception):
    """Base error for ticket and queue operations."""


class InvalidServiceTypeError(QueueError):
    """Raised when a service type is not one of the three supported types."""

    def __init__(self, service_type: object) -> None:
        self.service_type = service_type
        canonical = _join(list(SERVICE_TYPES), "or")
        aliases = ", ".join(SPANISH_ALIASES[service] for service in SERVICE_TYPES)
        super().__init__(
            f"Invalid service type {service_type!r}. "
            f"Use {canonical} (aliases: {aliases})."
        )


class EmptyQueueError(QueueError):
    """Raised when ``call_next`` removes from an empty service queue."""

    def __init__(self, service_type: str) -> None:
        self.service_type = service_type
        super().__init__(f"No clients are waiting for service {service_type!r}.")


class InvalidClientNameError(QueueError):
    """Raised when a ticket is issued without a client name."""

    def __init__(self) -> None:
        super().__init__("Client name cannot be empty.")


class _InputEnded(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


@dataclass(frozen=True, slots=True)
class Ticket:
    """One numbered client waiting for a single service type."""

    number: int
    client_name: str
    service_type: str
    issued_at: datetime


class BranchQueue:
    """One deque per service type and a single global ticket counter.

    ``call_next`` claims a client by removing the head with ``popleft``
    before the ticket is returned. DESIGN.md explains why that order matters
    when two agents call the same service together.
    """

    def __init__(self) -> None:
        self._queues: dict[str, deque[Ticket]] = {
            service: deque() for service in SERVICE_TYPES
        }
        self._next_number = 1

    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """Enqueue a new ticket and return it. The counter advances only then."""
        canonical = normalize_service_type(service_type)
        name = _clean_client_name(client_name)
        ticket = Ticket(
            number=self._next_number,
            client_name=name,
            service_type=canonical,
            issued_at=datetime.now(timezone.utc),
        )
        self._queues[canonical].append(ticket)
        self._next_number += 1
        return ticket

    def call_next(self, service_type: str) -> Ticket:
        """Remove and return the client who has waited longest for this service.

        The removal itself is the claim. An empty queue raises
        ``EmptyQueueError`` instead of leaking ``IndexError``.
        """
        canonical = normalize_service_type(service_type)
        try:
            return self._queues[canonical].popleft()
        except IndexError:
            raise EmptyQueueError(canonical) from None

    def peek_next(self, service_type: str) -> Ticket | None:
        """Return who is next for this service without removing them.

        An empty queue returns ``None``. An unknown service type still raises
        ``InvalidServiceTypeError``.
        """
        canonical = normalize_service_type(service_type)
        queue = self._queues[canonical]
        if not queue:
            return None
        return queue[0]

    def list_waiting(self) -> dict[str, list[Ticket]]:
        """Copy of each service queue, head first. The caller cannot mutate it."""
        return {service: list(self._queues[service]) for service in SERVICE_TYPES}

    def stats(self) -> dict[str, int]:
        """Waiting counts per service plus ``total``."""
        counts = {service: len(self._queues[service]) for service in SERVICE_TYPES}
        counts["total"] = sum(counts.values())
        return counts


def normalize_service_type(service_type: object) -> str:
    """Map an official English or Spanish service literal to the canonical id."""
    if not isinstance(service_type, str):
        raise InvalidServiceTypeError(service_type)
    key = _fold_token(service_type)
    try:
        return _ALIAS_TO_CANONICAL[key]
    except KeyError:
        raise InvalidServiceTypeError(service_type) from None


def _fold_token(value: str) -> str:
    lowered = value.strip().lower()
    for source, target in (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ü", "u"),
    ):
        lowered = lowered.replace(source, target)
    return "_".join(lowered.split())


def _clean_client_name(client_name: object) -> str:
    if not isinstance(client_name, str):
        raise InvalidClientNameError()
    name = " ".join(client_name.split())
    if not name:
        raise InvalidClientNameError()
    return name


def _join(items: list[str], conjunction: str) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" {conjunction} " + items[-1]


def _field(label: str, value: object) -> str:
    return f"  {label + ':':<12}{value}"


def format_ticket_lines(ticket: Ticket, lang: str) -> list[str]:
    label = LABELS[lang][ticket.service_type]
    issued = ticket.issued_at.isoformat(timespec="seconds")
    service = f"{ticket.service_type} ({label})"
    if lang == "es":
        rows = (
            ("Número", str(ticket.number)),
            ("Cliente", ticket.client_name),
            ("Servicio", service),
            ("Emitido", issued),
        )
    else:
        rows = (
            ("Number", str(ticket.number)),
            ("Client", ticket.client_name),
            ("Service", service),
            ("Issued", issued),
        )
    return [_field(name, value) for name, value in rows]


def format_queue_place(position: int, lang: str) -> str:
    if position < 1:
        raise ValueError("position must be >= 1")
    ahead = position - 1
    if lang == "es":
        if position == 1:
            return "  En cola:    1 esperando; es el siguiente en ser llamado."
        return (
            f"  En cola:    {position} esperando; "
            f"hay {ahead} delante, en orden de llegada."
        )
    if position == 1:
        return "  In queue:   1 waiting; this ticket is next."
    return f"  In queue:   {position} waiting; {ahead} ahead, in arrival order."


def format_issued(ticket: Ticket, position: int, lang: str) -> str:
    title = "Ticket emitido" if lang == "es" else "Ticket issued"
    lines = [title, "-" * len(title), *format_ticket_lines(ticket, lang)]
    lines.append(format_queue_place(position, lang))
    return "\n".join(lines)


def format_called(ticket: Ticket, lang: str) -> str:
    title = "Cliente llamado" if lang == "es" else "Client called"
    lines = [title, "-" * len(title), *format_ticket_lines(ticket, lang)]
    if lang == "es":
        lines.append("  Ya no está en la cola.")
    else:
        lines.append("  Removed from the queue.")
    return "\n".join(lines)


def format_peek(ticket: Ticket, lang: str) -> str:
    title = (
        "Siguiente en espera (no se retira)"
        if lang == "es"
        else "Next in line (not removed)"
    )
    lines = [title, "-" * len(title), *format_ticket_lines(ticket, lang)]
    if lang == "es":
        lines.append("  Sigue en la cola.")
    else:
        lines.append("  Still in the queue.")
    return "\n".join(lines)


def format_waiting(snapshot: dict[str, list[Ticket]], lang: str) -> str:
    lines: list[str] = []
    if lang == "es":
        lines.append("Lista de espera")
        lines.append("Dentro de cada servicio, el primero es el siguiente en ser llamado.")
    else:
        lines.append("Waiting list")
        lines.append("Within each service, the first ticket is called next.")
    total = 0
    for service in SERVICE_TYPES:
        tickets = snapshot[service]
        total += len(tickets)
        label = LABELS[lang][service]
        if lang == "es":
            lines.append(f"{label} ({service}) — {len(tickets)} en espera")
            empty = "  (nadie en espera)"
        else:
            lines.append(f"{label} ({service}) — {len(tickets)} waiting")
            empty = "  (nobody waiting)"
        if not tickets:
            lines.append(empty)
            continue
        for ticket in tickets:
            issued = ticket.issued_at.isoformat(timespec="seconds")
            lines.append(f"  #{ticket.number:<4} {ticket.client_name}    {issued}")
    if lang == "es":
        lines.append(f"Total en espera: {total}")
        if total == 0:
            lines.append("Siguiente paso: opción 1 para emitir un ticket.")
    else:
        lines.append(f"Waiting total: {total}")
        if total == 0:
            lines.append("Next step: choose 1 to issue a ticket.")
    return "\n".join(lines)


def format_stats(counts: dict[str, int], lang: str) -> str:
    title = "Estadísticas" if lang == "es" else "Statistics"
    labels = [
        f"{service} ({LABELS[lang][service]})" for service in SERVICE_TYPES
    ]
    width = max(len(label) for label in labels)
    lines = [title, "-" * len(title)]
    for service, label in zip(SERVICE_TYPES, labels):
        lines.append(f"  {label:<{width}}  {counts[service]}")
    lines.append(f"  {'total':<{width}}  {counts['total']}")
    return "\n".join(lines)


def format_menu(lang: str) -> str:
    if lang == "es":
        subtitle = "Cola de servicio etiquetada. Cada agente llama solo a su tipo."
    else:
        subtitle = "Tagged service queue. Each agent calls only their own service type."
    lines = ["Branch Queue", subtitle, "-" * 64]
    for key, labels in _MENU:
        lines.append(f"{key}  {labels[lang]}")
    return "\n".join(lines)


def format_help(lang: str) -> str:
    canonical = "\n".join(f"  {service}" for service in SERVICE_TYPES)
    aliases = "\n".join(
        f"  {SPANISH_ALIASES[service]} -> {service}" for service in SERVICE_TYPES
    )
    if lang == "es":
        title = "Ayuda"
        body = f"""Tipos canónicos (README en inglés):
{canonical}
Alias del README en español. Se guardan con el id canónico:
{aliases}
También valen mayúsculas, acentos y espacios internos:
  "Retiro", "depósito", "account management".

Ejemplo:
  Opción 1, nombre Ana Ruiz, servicio deposit.
  El ticket entra al final de la cola de depósitos.
  Opción 2, servicio deposit, llama a quien lleva más tiempo
  esperando en depósitos. No llama a retiros ni a gestión de cuenta.

La opción 5 muestra el siguiente sin retirarlo.
La opción 3 agrupa la espera. La opción 4 muestra conteos y total.
La opción 0 cierra la sesión. No se guarda nada en disco."""
    else:
        title = "Help"
        body = f"""Canonical types (English README):
{canonical}
Spanish README aliases. They are stored as the canonical id:
{aliases}
Case, accents, and internal spaces are accepted:
  "Retiro", "depósito", "account management".

Example:
  Option 1, name Ana Ruiz, service deposit.
  The ticket joins the end of the deposits queue.
  Option 2, service deposit, calls whoever has waited longest
  for deposits. It does not call withdrawals or account management.

Option 5 shows the next client without removing them.
Option 3 groups the waiting room. Option 4 shows counts and the total.
Option 0 ends the session. Nothing is written to disk."""
    return title + "\n" + ("-" * len(title)) + "\n" + body


def empty_queue_message(service: str, lang: str) -> str:
    label = LABELS[lang][service]
    if lang == "es":
        return f"No hay clientes esperando para {label} ({service})."
    return f"No clients are waiting for {label} ({service})."


def invalid_service_message(service_type: object, lang: str) -> str:
    canonical = _join(list(SERVICE_TYPES), "o" if lang == "es" else "or")
    aliases = ", ".join(SPANISH_ALIASES[service] for service in SERVICE_TYPES)
    if lang == "es":
        return (
            f"Tipo de servicio no válido: {service_type!r}. "
            f"Usa {canonical} (alias: {aliases})."
        )
    return (
        f"Invalid service type: {service_type!r}. "
        f"Use {canonical} (aliases: {aliases})."
    )


def invalid_name_message(lang: str) -> str:
    if lang == "es":
        return "El nombre del cliente no puede estar vacío."
    return "Client name cannot be empty."


def invalid_option_message(raw: str, lang: str) -> str:
    if lang == "es":
        return f"Opción no reconocida: {raw!r}. Usa 1, 2, 3, 4, 5, 6, 7 o 0."
    return f"Unrecognized option: {raw!r}. Use 1, 2, 3, 4, 5, 6, 7, or 0."


def closed_message(lang: str, reason: str) -> str:
    if lang == "es":
        if reason == "interrupt":
            return "Interrupción. Sesión terminada sin guardar."
        return "Fin de la entrada. Sesión terminada sin guardar."
    if reason == "interrupt":
        return "Interrupted. Session ended without saving."
    return "End of input. Session ended without saving."


def bye_message(lang: str) -> str:
    if lang == "es":
        return "Sesión terminada. Los tickets solo existían en memoria."
    return "Session ended. Tickets existed only in memory."


def _show(text: str) -> None:
    print(f"\n{text}", flush=True)


def _read_line(prompt: str) -> str:
    """Read one line. A terminal echoes the keys; a pipe does not, so echo it."""
    try:
        value = input(prompt)
    except EOFError:
        print(flush=True)
        raise _InputEnded("eof")
    except KeyboardInterrupt:
        print(flush=True)
        raise _InputEnded("interrupt")
    if not sys.stdin.isatty():
        print(value, flush=True)
    return value


def _service_hint(lang: str) -> str:
    canonical = ", ".join(SERVICE_TYPES)
    aliases = ", ".join(SPANISH_ALIASES[service] for service in SERVICE_TYPES)
    if lang == "es":
        return f"Canónico: {canonical}. Alias: {aliases}."
    return f"Canonical: {canonical}. Aliases: {aliases}."


def _read_service(lang: str) -> str:
    print(_service_hint(lang), flush=True)
    prompt = "Servicio: " if lang == "es" else "Service: "
    return _read_line(prompt)


def _issue_flow(branch: BranchQueue, lang: str) -> None:
    name_prompt = "Nombre del cliente: " if lang == "es" else "Client name: "
    name = _read_line(name_prompt)
    if not " ".join(name.split()):
        _show(invalid_name_message(lang))
        return
    service = _read_service(lang)
    try:
        ticket = branch.issue_ticket(name, service)
    except InvalidServiceTypeError as exc:
        _show(invalid_service_message(exc.service_type, lang))
        return
    position = len(branch.list_waiting()[ticket.service_type])
    _show(format_issued(ticket, position, lang))


def _call_flow(branch: BranchQueue, lang: str) -> None:
    service = _read_service(lang)
    try:
        ticket = branch.call_next(service)
    except InvalidServiceTypeError as exc:
        _show(invalid_service_message(exc.service_type, lang))
        return
    except EmptyQueueError as exc:
        _show(empty_queue_message(exc.service_type, lang))
        return
    _show(format_called(ticket, lang))


def _peek_flow(branch: BranchQueue, lang: str) -> None:
    service = _read_service(lang)
    try:
        ticket = branch.peek_next(service)
    except InvalidServiceTypeError as exc:
        _show(invalid_service_message(exc.service_type, lang))
        return
    if ticket is None:
        _show(empty_queue_message(normalize_service_type(service), lang))
        return
    _show(format_peek(ticket, lang))


def _menu_loop(branch: BranchQueue, lang: str) -> int:
    while True:
        print(format_menu(lang), flush=True)
        prompt = "Opción: " if lang == "es" else "Option: "
        try:
            raw = _read_line(prompt)
        except _InputEnded as ended:
            _show(closed_message(lang, ended.reason))
            return 0
        choice = raw.strip().lower()
        try:
            if choice == "0":
                _show(bye_message(lang))
                return 0
            if choice == "7":
                lang = "en" if lang == "es" else "es"
                continue
            if choice == "1":
                _issue_flow(branch, lang)
            elif choice == "2":
                _call_flow(branch, lang)
            elif choice == "3":
                _show(format_waiting(branch.list_waiting(), lang))
            elif choice == "4":
                _show(format_stats(branch.stats(), lang))
            elif choice == "5":
                _peek_flow(branch, lang)
            elif choice == "6":
                _show(format_help(lang))
            else:
                _show(invalid_option_message(choice, lang))
        except _InputEnded as ended:
            _show(closed_message(lang, ended.reason))
            return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tagged service queue for a bank-branch terminal."
    )
    parser.add_argument(
        "--lang",
        choices=("es", "en"),
        default="es",
        help="Menu language. Default: es. Service ids stay in English either way.",
    )
    args = parser.parse_args(argv)
    return _menu_loop(BranchQueue(), args.lang)


if __name__ == "__main__":
    sys.exit(main())
