"""
Auxiliary helper functions
"""


def chain_until(typeclass, ignores, *iterables):
    """
    Flattens/chains iterables recursively until it becomes a certain type. Optionally ignores particular types.
    """
    for each_iterable in iterables:
        if isinstance(each_iterable, typeclass):
            yield each_iterable
        elif not isinstance(each_iterable, ignores):
            # breakpoint()
            return chain_until(
                typeclass,
                ignores,
                *[x for x in each_iterable if not isinstance(each_iterable, ignores)]
            )
