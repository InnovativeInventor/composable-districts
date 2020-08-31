import geocompose
import postal.expand as expand
import secrets
import pytest


def test_normalize_validator():
    address = "1600 Pennsylvania Ave NW, Washington, DC United States"
    normalized_address = geocompose.normalize(address)

    assert geocompose.Address(name=normalized_address, location=(0, 0))

    # pytest exceptions
    with pytest.raises(ValueError):
        geocompose.Address(name=address, location=(0, 0))

    with pytest.raises(ValueError):
        geocompose.Address(name=normalized_address, location="should fail")


def test_equality_random():
    address = "1600 Pennsylvania Ave NW, Washington, DC 20500, United States"
    address_expanded = secrets.choice(expand.expand_address(address))
    print(geocompose.normalize(address_expanded), geocompose.normalize(address))

    address_1 = geocompose.Address(
        name=geocompose.normalize(address_expanded), location=(0, 0)
    )

    address_2 = geocompose.Address(name=geocompose.normalize(address), location=(0, 0))

    assert address_2 == address_1
