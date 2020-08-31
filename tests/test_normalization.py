import geocompose

def test_normalize():
    address = "1600 Pennsylvania Ave NW, Washington, DC 20500-0003, United States"
    normalized_address = geocompose.normalize(address)
    print(normalized_address)
    raise ValueError()
    assert geocompose.Address(name=normalized_address, location=(0,0))
