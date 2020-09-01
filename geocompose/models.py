from pydantic import BaseModel, validator
from typing import Optional, Set
from postal.dedupe import is_name_duplicate as equals
from geocompose.definitions import normalize
import shapely


class Address(BaseModel):
    location: tuple  # of coordinates
    name: str  # normalized, human-readable string
    polygon: Optional[str]  # hash of the precinct or some other uuid

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
