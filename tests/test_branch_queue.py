"""Core queue behavior: numbering, FIFO per tag, empty queues, invalid tags."""

from datetime import datetime, timezone

import pytest

from branch_queue import (
    SERVICE_TYPES,
    BranchQueue,
    EmptyQueueError,
    InvalidClientNameError,
    InvalidServiceTypeError,
    Ticket,
)


def test_ticket_records_number_name_service_and_timestamp():
    branch = BranchQueue()
    before = datetime.now(timezone.utc)
    ticket = branch.issue_ticket("  Ana   Ruiz\n", "withdrawal")
    after = datetime.now(timezone.utc)

    assert isinstance(ticket, Ticket)
    assert ticket.number == 1
    assert ticket.client_name == "Ana Ruiz"
    assert ticket.service_type == "withdrawal"
    assert isinstance(ticket.issued_at, datetime)
    assert ticket.issued_at.tzinfo is not None
    assert before <= ticket.issued_at <= after


def test_ticket_numbers_are_global_and_start_at_one():
    branch = BranchQueue()
    numbers = [
        branch.issue_ticket("A", "deposit").number,
        branch.issue_ticket("B", "withdrawal").number,
        branch.issue_ticket("C", "gestion_cuenta").number,
    ]
    assert numbers == [1, 2, 3]
    assert len(set(numbers)) == 3


def test_one_deque_per_service_and_call_next_pops_the_head():
    from collections import deque

    branch = BranchQueue()
    assert set(branch._queues) == set(SERVICE_TYPES)
    for service in SERVICE_TYPES:
        assert isinstance(branch._queues[service], deque)
        assert len(branch._queues[service]) == 0

    ticket = branch.issue_ticket("Ana", "deposit")
    assert branch._queues["deposit"][0] is ticket
    assert branch.call_next("deposit") is ticket
    assert len(branch._queues["deposit"]) == 0
    assert len(branch._queues["withdrawal"]) == 0


def test_fifo_order_per_service_tag():
    branch = BranchQueue()
    first = branch.issue_ticket("Ana", "deposit")
    branch.issue_ticket("Bea", "withdrawal")
    second = branch.issue_ticket("Carlos", "deposito")
    branch.issue_ticket("Dina", "account_management")
    third = branch.issue_ticket("Eva", "DEPOSIT")

    assert [ticket.number for ticket in branch.list_waiting()["deposit"]] == [
        first.number,
        second.number,
        third.number,
    ]
    assert branch.call_next("deposit") == first
    assert branch.call_next("deposit") == second
    assert branch.call_next("deposit") == third
    with pytest.raises(EmptyQueueError):
        branch.call_next("deposit")

    assert [ticket.client_name for ticket in branch.list_waiting()["withdrawal"]] == ["Bea"]
    assert [
        ticket.client_name for ticket in branch.list_waiting()["account_management"]
    ] == ["Dina"]


def test_call_next_does_not_take_another_services_client():
    branch = BranchQueue()
    deposit = branch.issue_ticket("Ana", "deposit")
    withdrawal = branch.issue_ticket("Bea", "withdrawal")

    called = branch.call_next("withdrawal")

    assert called == withdrawal
    assert branch.peek_next("deposit") == deposit
    assert [ticket.number for ticket in branch.list_waiting()["deposit"]] == [1]
    assert branch.list_waiting()["withdrawal"] == []


def test_peek_keeps_the_ticket_and_call_returns_that_same_ticket():
    branch = BranchQueue()
    ticket = branch.issue_ticket("Ana", "deposit")

    assert branch.peek_next("deposit") == ticket
    assert branch.peek_next("deposit") == ticket
    assert branch.stats()["deposit"] == 1
    assert branch.call_next("deposit") == ticket
    assert branch.peek_next("deposit") is None
    assert branch.stats()["total"] == 0


def test_call_next_removes_before_returning_so_the_same_client_is_not_reused():
    branch = BranchQueue()
    first = branch.issue_ticket("Ana", "deposit")
    second = branch.issue_ticket("Bea", "deposit")

    assert branch.call_next("deposit") == first
    assert first not in branch.list_waiting()["deposit"]
    assert branch.call_next("deposit") == second


def test_empty_queue_call_raises_and_peek_returns_none():
    branch = BranchQueue()
    branch.issue_ticket("Ana", "withdrawal")

    with pytest.raises(EmptyQueueError) as caught:
        branch.call_next("deposit")

    assert str(caught.value) == "No clients are waiting for service 'deposit'."
    assert branch.peek_next("deposit") is None
    assert branch.peek_next("account_management") is None
    assert branch.stats() == {
        "deposit": 0,
        "withdrawal": 1,
        "account_management": 0,
        "total": 1,
    }


@pytest.mark.parametrize(
    "raw",
    ["", "vip", "deposits", "cuenta", "loan", "gestion de cuenta", None, 3],
)
def test_invalid_service_tag_is_rejected(raw):
    branch = BranchQueue()

    with pytest.raises(InvalidServiceTypeError) as caught:
        branch.issue_ticket("Ana", raw)

    message = str(caught.value)
    assert "deposit" in message
    assert "withdrawal" in message
    assert "account_management" in message
    assert "deposito" in message
    assert branch.stats()["total"] == 0
    assert branch.list_waiting() == {
        "deposit": [],
        "withdrawal": [],
        "account_management": [],
    }


def test_invalid_service_on_call_or_peek_is_not_an_empty_queue():
    branch = BranchQueue()
    branch.issue_ticket("Ana", "deposit")

    with pytest.raises(InvalidServiceTypeError):
        branch.call_next("vip")
    with pytest.raises(InvalidServiceTypeError):
        branch.peek_next("vip")

    assert branch.stats()["total"] == 1


def test_rejected_issue_does_not_consume_a_number():
    branch = BranchQueue()
    with pytest.raises(InvalidServiceTypeError):
        branch.issue_ticket("Ana", "vip")
    with pytest.raises(InvalidClientNameError) as caught:
        branch.issue_ticket("   ", "deposit")

    assert str(caught.value) == "Client name cannot be empty."
    assert branch.issue_ticket("Ana", "deposit").number == 1


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("deposit", "deposit"),
        ("Deposit", "deposit"),
        ("deposito", "deposit"),
        ("depósito", "deposit"),
        ("withdrawal", "withdrawal"),
        ("  Retiro  ", "withdrawal"),
        ("account_management", "account_management"),
        ("account management", "account_management"),
        ("gestion_cuenta", "account_management"),
        ("gestión_cuenta", "account_management"),
    ],
)
def test_spanish_and_english_literals_share_a_queue(raw, canonical):
    branch = BranchQueue()
    ticket = branch.issue_ticket("Ana", raw)
    assert ticket.service_type == canonical
    assert branch.list_waiting()[canonical] == [ticket]


def test_operations_accept_the_spanish_readme_literals():
    branch = BranchQueue()
    deposit = branch.issue_ticket("Ana", "deposito")
    withdrawal = branch.issue_ticket("Bea", "retiro")
    account = branch.issue_ticket("Ciro", "gestion_cuenta")

    assert branch.peek_next("deposito") == deposit
    assert branch.call_next("retiro") == withdrawal
    assert branch.stats()["account_management"] == 1
    assert branch.list_waiting()["account_management"] == [account]
    assert [ticket.number for ticket in (deposit, withdrawal, account)] == [1, 2, 3]


def test_list_waiting_is_grouped_ordered_and_isolated():
    branch = BranchQueue()
    first = branch.issue_ticket("Ana", "deposit")
    branch.issue_ticket("Bea", "withdrawal")
    second = branch.issue_ticket("Carlos", "deposit")

    snapshot = branch.list_waiting()
    assert list(snapshot) == list(SERVICE_TYPES)
    assert snapshot["deposit"] == [first, second]
    assert type(snapshot["deposit"]) is list

    snapshot["deposit"].clear()
    assert [ticket.number for ticket in branch.list_waiting()["deposit"]] == [1, 3]


def test_stats_counts_each_service_and_total():
    branch = BranchQueue()
    assert branch.stats() == {
        "deposit": 0,
        "withdrawal": 0,
        "account_management": 0,
        "total": 0,
    }
    branch.issue_ticket("A", "deposit")
    branch.issue_ticket("B", "deposit")
    branch.issue_ticket("C", "retiro")
    branch.call_next("deposit")

    assert branch.stats() == {
        "deposit": 1,
        "withdrawal": 1,
        "account_management": 0,
        "total": 2,
    }


def test_interleaved_twenty_tickets_keep_unique_numbers_and_per_tag_fifo():
    branch = BranchQueue()
    services = ("deposit", "retiro", "account_management", "deposito", "withdrawal")
    issued: dict[str, list[int]] = {service: [] for service in SERVICE_TYPES}
    order: list[int] = []
    for index in range(20):
        service = services[index % len(services)]
        ticket = branch.issue_ticket(f"Cliente {index}", service)
        order.append(ticket.number)
        issued[ticket.service_type].append(ticket.number)

    assert order == list(range(1, 21))
    assert len(set(order)) == 20
    for service in SERVICE_TYPES:
        waiting = [ticket.number for ticket in branch.list_waiting()[service]]
        assert waiting == issued[service]
        while issued[service]:
            called = branch.call_next(service)
            assert called.number == issued[service].pop(0)
