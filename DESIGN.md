# Diseño — Branch Queue

La estructura es una `collections.deque` independiente por cada tipo de servicio, más un contador entero global para el número de ticket.

Los identificadores canónicos son los del enunciado en inglés: `deposit`, `withdrawal` y `account_management`. Los literales del enunciado en español (`deposito`, `retiro`, `gestion_cuenta`) entran a la misma cola y se guardan con el id canónico. Así los dos README oficiales hablan de las mismas tres colas.

## Por qué no una lista compartida

Una sola lista ordenada por llegada mezcla depósitos, retiros y gestión de cuenta. Cuando el agente de depósitos llama al siguiente, el programa recorre esa lista hasta encontrar el primer depósito. En el peor caso mira a las *n* personas de la sucursal, aunque casi todas esperen otro servicio. Quitar a alguien del medio de una lista también desplaza al resto: otra pasada lineal.

Con una cola por servicio, el agente no ve a los clientes de los demás. `issue_ticket` hace `append` al final de su deque. `call_next` hace `popleft` de esa misma deque. Las dos operaciones son O(1) y no dependen de cuánta gente espere en los otros servicios. El orden de llegada ya quedó fijado al emitir: no hace falta ordenar.

Eso es lo que pide la sucursal del enunciado: llamar al siguiente de *su* servicio sin recorrer la sala.

| Operación | Lista compartida | Una deque por servicio |
| --- | --- | --- |
| Emitir | O(1) al final, si no se reordena | O(1) `append` |
| `call_next` | O(n) para buscar y compactar | O(1) `popleft` |
| `peek_next` | O(n) para buscar | O(1) leer la cabeza |
| `list_waiting` | O(n) | O(n) para copiar lo que hay |
| `stats` | O(n) si hay que contar | O(1) con la longitud de cada deque |
| Memoria | O(n) | O(n) |

El espacio total sigue siendo proporcional a la gente en espera. Lo que cambia es el coste de llamar al siguiente.

## Dos agentes, el mismo servicio, el mismo instante

La CLI de este programa es un solo hilo: un comando termina antes de que empiece el siguiente. La pregunta del enunciado es la otra situación: dos agentes de depósitos ejecutan `call_next("deposit")` a la vez sobre la cola `[Ana, Bea]`.

Si los dos leen primero la cabeza, los dos ven a Ana. Quitar el elemento después de esa lectura compartida no tiene un dueño: los dos pueden llevarse a Ana, o uno puede borrar al cliente que el otro ya creyó suyo.

La primera mutación de estado es el retiro de la cabeza de esa cola (`popleft`). Ese retiro tiene que ocurrir en exclusión antes de entregar el ticket y antes de que el otro agente lea o modifique la misma cola. Quien completa el `popleft` recibe a Ana. El otro, cuando entra, retira a Bea o encuentra la cola vacía. No sirve marcar el ticket como "llamado" después de que los dos ya lo leyeron: la reserva es la extracción, no un aviso posterior.

El contador global no interviene aquí. Solo avanza en `issue_ticket`, y solo si el nombre y el servicio son válidos. Las otras colas tampoco se tocan: el agente de retiros puede hacer `popleft` de la suya al mismo tiempo.

En el código, `call_next` no hace peek y luego borra. Intenta `popleft`. Si la deque está vacía, `IndexError` se sustituye por `EmptyQueueError` con el servicio en el mensaje. `peek_next` solo lee. Si no hay nadie, devuelve `None` y no lanza: el enunciado pide el error significativo en `call_next`, y pide que mirar una cola vacía no rompa el programa.

Un integrador con hilos reales tiene que envolver ese `popleft` en un cerrojo de esa cola. Este programa no lo hace: no hay dos agentes en paralelo y el enunciado no pide asignación de agentes ni concurrencia implementada. El cerrojo, si se añade, debe cubrir solo la extracción, no la lista de otros servicios.

## Contador y vacíos

- El primer ticket es el 1. El número es global: depósito 1, retiro 2, depósito 3.
- Un servicio inválido o un nombre vacío no consume número.
- `list_waiting` siempre trae las tres claves, aunque la lista esté vacía, y devuelve copias.
- `stats` siempre trae las tres claves y `"total"`.

## English

The structure is one `collections.deque` per service type plus one global ticket counter.

Canonical ids come from the English README: `deposit`, `withdrawal`, `account_management`. The Spanish README literals (`deposito`, `retiro`, `gestion_cuenta`) join that same queue and are stored under the canonical id.

A single shared list ordered by arrival mixes every service. `call_next("deposit")` then scans all *n* waiting clients and, on a plain list, pays another linear shift to delete from the middle. One deque per service makes `append` and `popleft` O(1) no matter how many people are waiting for something else. Arrival order is the order of `append`. No sort step.

The CLI is single-threaded, so two menu commands cannot overlap. The assignment still asks what happens if two agents of the same service call `call_next` at the same moment. If both read the head first, both see the same client. The first state mutation is the removal of that queue's head (`popleft`). That removal must finish, under mutual exclusion, before the ticket is handed out and before the other agent reads or mutates the same queue. The agent whose `popleft` succeeds owns the client. The other then pops the new head or observes an empty queue. Updating a "called" flag after a shared read does not prevent the double call. The global counter is not part of this mutation; it changes only when a ticket is issued. Other service queues stay untouched.

`call_next` pops first and raises `EmptyQueueError` when the deque is empty. `peek_next` is a read and returns `None` on an empty queue. A future threaded host must lock that `popleft`. This program does not ship that lock: agent assignment and a concurrent runtime are outside the assignment, and the terminal handles one command at a time.
