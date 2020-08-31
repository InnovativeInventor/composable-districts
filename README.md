
# Table of Contents

1.  [Overview](#org870dbc7)
2.  [Operations](#orga7ab978)
    1.  [Merge Operation](#org7f3d75e)
    2.  [Diff Operation (from and address-based representation)](#org5a48e7b)
    3.  [Diff Operation (from a polygon representation)](#orgbb3bb95)
        1.  [The diff between two shapefiles are calculated by first converting to an address-based representation, then utilizing the previously defined diff operation on the address-based representation.](#orga839126)
    4.  [Voronoi Diagram](#org9746c83)



<a id="org870dbc7"></a>

# Overview


<a id="orga7ab978"></a>

# Operations


<a id="org7f3d75e"></a>

## Merge Operation

To merge, the address containing the most information when parsed (using libpostal) will added to the output address.
An address-location pair is considered a duplicate if two conditions are satisfied:

1.  The two addresses normalize to the same (or similar) string using libpostal

2.  The two addresses are geographically within 1 kilometer of each other


<a id="org5a48e7b"></a>

## Diff Operation (from and address-based representation)

The diff operation is intended primarily for visualization purposes.

If the intersection between the two regions is greater than half of the size of either region, then the the two regions are considered to be the same.
The difference is the [symmetric difference](https://shapely.readthedocs.io/en/latest/manual.html#object.symmetric_difference) between the two regions.

If not, the intersection of the two regions is the difference.

Finally, if one of the regions completely contains the other, the symmetric difference is used.


<a id="orgbb3bb95"></a>

## Diff Operation (from a polygon representation)


<a id="orga839126"></a>

### The diff between two shapefiles are calculated by first converting to an address-based representation, then utilizing the previously defined diff operation on the address-based representation.


<a id="org9746c83"></a>

## Voronoi Diagram

In order to visualize an address-based representation of districts better, a voronoi diagram can be used to create a polygon representation of the geographical region.

