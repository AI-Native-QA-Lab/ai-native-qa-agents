"""Minimal checkout behavior for the v0.4 reference assessment."""


def checkout(payment_declined: bool) -> str:
    if payment_declined:
        return "declined"
    return "paid"
