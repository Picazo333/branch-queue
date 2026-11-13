# Branch Queue

Gestor de cola en terminal para el ejercicio Branch Queue de 4Geeks Academy. Cada tipo de servicio tiene su propia cola. Un agente llama al cliente que lleva más tiempo esperando *ese* servicio, sin recorrer el resto de la sala.

Los identificadores canónicos son `deposit`, `withdrawal` y `account_management`. Los literales `deposito`, `retiro` y `gestion_cuenta` entran en la misma cola y se guardan con el id canónico. La nota de complejidad y de llamadas simultáneas está en [DESIGN.md](DESIGN.md).

El programa usa solo la biblioteca estándar de Python (`collections.deque`, `datetime`). No escribe en disco: al salir, la cola desaparece.

## Español

### Requisitos

- Python 3.10 o posterior. Esta entrega se ejecutó con Python 3.12.3.
- Ningún paquete para usar el programa.
- `pytest` solo para la suite. No lo importa `branch_queue.py`.

### Ejecutar

Desde la raíz del repositorio:

```bash
python3 branch_queue.py
```

Menú en inglés (los ids de servicio no cambian):

```bash
python3 branch_queue.py --lang en
```

Salir: opción `0`. Si la entrada se cierra, el proceso termina sin traceback.

### Menú

| Opción | Acción |
| --- | --- |
| 1 | Pregunta el nombre y el servicio, y emite un ticket. |
| 2 | Llama al siguiente de un servicio y lo saca de la cola. |
| 3 | Lista la espera agrupada. El primero de cada grupo es el siguiente. |
| 4 | Muestra el conteo por servicio y el total. |
| 5 | Muestra el siguiente sin retirarlo. |
| 6 | Ayuda con los literales y un ejemplo. |
| 7 | Cambia el idioma del menú. |
| 0 | Termina. No guarda nada. |

Un servicio desconocido o un nombre vacío no emite ticket y no consume número. Llamar a un servicio vacío muestra el mensaje y vuelve al menú.

### Sesión reproducible

```bash
python3 branch_queue.py --lang es <<'EOF'
1
Ana Ruiz
deposit
1
Bea Sol
retiro
3
4
2
deposit
2
deposit
0
EOF
```

Ana entra en depósitos y Bea, con el alias `retiro`, en retiros. La lista y las estadísticas salen antes de las llamadas. La primera llamada con `deposit` atiende a Ana. La segunda llamada con `deposit` no atiende a Bea: la cola de depósitos ya está vacía.

Salida real de ese comando. La hora de `Emitido` cambia en cada ejecución; esta corrida es `2026-11-06T12:16:14+00:00`:

```text
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 1
Nombre del cliente: Ana Ruiz
Canónico: deposit, withdrawal, account_management. Alias: deposito, retiro, gestion_cuenta.
Servicio: deposit

Ticket emitido
--------------
  Número:     1
  Cliente:    Ana Ruiz
  Servicio:   deposit (Depósitos)
  Emitido:    2026-11-06T12:16:14+00:00
  En cola:    1 esperando; es el siguiente en ser llamado.
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 1
Nombre del cliente: Bea Sol
Canónico: deposit, withdrawal, account_management. Alias: deposito, retiro, gestion_cuenta.
Servicio: retiro

Ticket emitido
--------------
  Número:     2
  Cliente:    Bea Sol
  Servicio:   withdrawal (Retiros)
  Emitido:    2026-11-06T12:16:14+00:00
  En cola:    1 esperando; es el siguiente en ser llamado.
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 3

Lista de espera
Dentro de cada servicio, el primero es el siguiente en ser llamado.
Depósitos (deposit) — 1 en espera
  #1    Ana Ruiz    2026-11-06T12:16:14+00:00
Retiros (withdrawal) — 1 en espera
  #2    Bea Sol    2026-11-06T12:16:14+00:00
Gestión de cuenta (account_management) — 0 en espera
  (nadie en espera)
Total en espera: 2
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 4

Estadísticas
------------
  deposit (Depósitos)                     1
  withdrawal (Retiros)                    1
  account_management (Gestión de cuenta)  0
  total                                   2
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 2
Canónico: deposit, withdrawal, account_management. Alias: deposito, retiro, gestion_cuenta.
Servicio: deposit

Cliente llamado
---------------
  Número:     1
  Cliente:    Ana Ruiz
  Servicio:   deposit (Depósitos)
  Emitido:    2026-11-06T12:16:14+00:00
  Ya no está en la cola.
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 2
Canónico: deposit, withdrawal, account_management. Alias: deposito, retiro, gestion_cuenta.
Servicio: deposit

No hay clientes esperando para Depósitos (deposit).
Branch Queue
Cola de servicio etiquetada. Cada agente llama solo a su tipo.
----------------------------------------------------------------
1  Emitir ticket
2  Llamar al siguiente cliente
3  Ver la lista de espera
4  Ver estadísticas
5  Ver el siguiente sin retirarlo
6  Ayuda
7  Cambiar idioma (ahora: español)
0  Salir
Opción: 0

Sesión terminada. Los tickets solo existían en memoria.
```

### Pruebas

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

La segunda orden se ejecuta en la raíz del repositorio. Tiene que terminar sin fallos.

### Estructura

| Archivo | Papel |
| --- | --- |
| `branch_queue.py` | `Ticket`, `BranchQueue` y el menú. Punto de entrada. |
| `DESIGN.md` | Por qué una deque por servicio, y qué mutación va primero si dos agentes llaman a la vez. |
| `tests/` | Operaciones, casos límite y sesiones reales de la CLI. |
| `pyproject.toml` | Paquete sin dependencias de ejecución. `pytest` queda como extra de desarrollo. |

### Decisiones

- Una `collections.deque` por servicio. `call_next` hace `popleft` antes de devolver el ticket.
- El número de ticket es un contador global que empieza en 1.
- `peek_next` sobre una cola vacía devuelve `None`. `call_next` lanza `EmptyQueueError`. El menú atrapa ese error y sigue.
- `list_waiting` devuelve copias. Quien lee la lista no modifica la cola.
- Si la entrada no es una terminal, cada línea leída se vuelve a imprimir. En una terminal la repite el propio teclado, y no se duplica.

## English

Terminal queue for the 4Geeks Academy Branch Queue exercise. Each service type has its own queue. An agent calls the client who has waited longest for *that* service.

Canonical ids are `deposit`, `withdrawal`, and `account_management`. The literals `deposito`, `retiro`, and `gestion_cuenta` join the same queue and are stored under the canonical id. Complexity and the simultaneous-call note are in [DESIGN.md](DESIGN.md).

The program uses only the Python standard library (`collections.deque`, `datetime`). It does not write to disk. The queue is gone when the process exits.

### Requirements

- Python 3.10 or newer. This delivery was run with Python 3.12.3.
- No packages are required to run the program.
- `pytest` runs the suite only. `branch_queue.py` does not import it.

### Run

From the repository root:

```bash
python3 branch_queue.py
```

English menu (service ids stay the same):

```bash
python3 branch_queue.py --lang en
```

Exit with option `0`. If input closes, the process ends without a traceback.

### Menu

| Option | Action |
| --- | --- |
| 1 | Asks for the client name and the service, then issues a ticket. |
| 2 | Calls the next client for a service and removes them. |
| 3 | Lists everyone waiting, grouped by service. The first of each group is next. |
| 4 | Shows the count per service and the total. |
| 5 | Shows the next client without removing them. |
| 6 | Help with the literals and an example. |
| 7 | Switches the menu language. |
| 0 | Exits. Nothing is saved. |

An unknown service or an empty name does not issue a ticket and does not consume a number. Calling an empty service prints the reason and returns to the menu.

### Reproducible session

```bash
python3 branch_queue.py --lang en <<'EOF'
1
Ann Cole
account_management
2
account_management
2
account_management
0
EOF
```

The first call attends Ann Cole. The second call finds that queue empty and says so. It does not raise an uncaught exception.

Real output of that command. The `Issued` timestamp changes on every run; this run is `2026-11-06T12:16:14+00:00`:

```text
Branch Queue
Tagged service queue. Each agent calls only their own service type.
----------------------------------------------------------------
1  Issue a ticket
2  Call the next client
3  Show the waiting list
4  Show statistics
5  Show the next client without removing them
6  Help
7  Switch language (now: English)
0  Exit
Option: 1
Client name: Ann Cole
Canonical: deposit, withdrawal, account_management. Aliases: deposito, retiro, gestion_cuenta.
Service: account_management

Ticket issued
-------------
  Number:     1
  Client:     Ann Cole
  Service:    account_management (Account management)
  Issued:     2026-11-06T12:16:14+00:00
  In queue:   1 waiting; this ticket is next.
Branch Queue
Tagged service queue. Each agent calls only their own service type.
----------------------------------------------------------------
1  Issue a ticket
2  Call the next client
3  Show the waiting list
4  Show statistics
5  Show the next client without removing them
6  Help
7  Switch language (now: English)
0  Exit
Option: 2
Canonical: deposit, withdrawal, account_management. Aliases: deposito, retiro, gestion_cuenta.
Service: account_management

Client called
-------------
  Number:     1
  Client:     Ann Cole
  Service:    account_management (Account management)
  Issued:     2026-11-06T12:16:14+00:00
  Removed from the queue.
Branch Queue
Tagged service queue. Each agent calls only their own service type.
----------------------------------------------------------------
1  Issue a ticket
2  Call the next client
3  Show the waiting list
4  Show statistics
5  Show the next client without removing them
6  Help
7  Switch language (now: English)
0  Exit
Option: 2
Canonical: deposit, withdrawal, account_management. Aliases: deposito, retiro, gestion_cuenta.
Service: account_management

No clients are waiting for Account management (account_management).
Branch Queue
Tagged service queue. Each agent calls only their own service type.
----------------------------------------------------------------
1  Issue a ticket
2  Call the next client
3  Show the waiting list
4  Show statistics
5  Show the next client without removing them
6  Help
7  Switch language (now: English)
0  Exit
Option: 0

Session ended. Tickets existed only in memory.
```

### Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Run the second command from the repository root. It must finish with no failures.

### Layout

| File | Role |
| --- | --- |
| `branch_queue.py` | `Ticket`, `BranchQueue`, and the menu. Entry point. |
| `DESIGN.md` | Why one deque per service, and which mutation must happen first if two agents call together. |
| `tests/` | Operations, edge cases, and real CLI sessions. |
| `pyproject.toml` | Package with no runtime dependencies. `pytest` is a dev extra. |

### Decisions

- One `collections.deque` per service. `call_next` uses `popleft` before it returns the ticket.
- Ticket numbers are a global counter starting at 1.
- `peek_next` on an empty queue returns `None`. `call_next` raises `EmptyQueueError`. The menu catches that error and continues.
- `list_waiting` returns copies, so a reader cannot change the queue.
- When input is not a terminal, each line read is printed back. A terminal already echoes the keys, so it is not printed twice.
