from typing import Set
from pydantic import BaseModel, validator, ValidationError
import shapely.geometry

# from postal.expand import expand_address as normalize
from postal.normalize import normalize_string as normalize
from postal.dedupe import is_name_duplicate as equals
from pydantic.dataclasses import dataclass


class Address(BaseModel):
    location: tuple  # of coordinates
    name: str  # normalized, human-readable string

    def __hash__(self):
        """
        A hash of the normalized address. Do not use hashes for deduplication.
        """
        return hash(normalize(self.name.replace(",", "")))

    def __eq__(self, other):
        # return hash(self) == hash(hash) # does not work well
        return equals(self.name, other.name, "en")

    @validator("name")
    def check_address_normalized(cls, name) -> bool:
        """
        Checks if the address is normalized
        """
        if normalize(name) == name:
            return name
        else:
            raise ValueError("Address is not normalized")


class Region(BaseModel):
    """
    A geographical region is represented by a set of addresses and 
    """

    addresses: Set[Address]
    polygon: shapely.geometry.polygon.Polygon

    class Config:
        arbitrary_types_allowed = True


# def normalize(address: str) -> str:
#     return postal.expand_address(address)
