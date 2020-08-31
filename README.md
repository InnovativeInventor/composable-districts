
# Table of Contents

1.  [Overview](#org680c7a1)
2.  [Operations](#orgf65c0f4)
    1.  [Merge Operation](#org92a5884)
    2.  [Diff Operation (from and address-based representation)](#org5ecfad3)
        1.  [If the intersection between the two regions is greater than half of the size of either region, then the the two regions are considered to be the same.](#org788216f)
        2.  [If not, the intersection of the two regions is the difference.](#org0a37281)
        3.  [If one of the regions completely contains the other, the symmetric difference is used.](#org7725db1)
    3.  [Diff Operation (from a polygon representation)](#org42a16ef)
        1.  [The diff between two shapefiles are calculated by first converting to an address-based representation, then utilizing the previously defined diff operation on the address-based representation.](#org5912123)
    4.  [Voronoi Diagram](#orgb7649b9)



<a id="org680c7a1"></a>

# Overview


<a id="orgf65c0f4"></a>

# Operations


<a id="org92a5884"></a>

## Merge Operation

To merge, the address containing the most information when parsed (using libpostal) will added to the output address.
An address-location pair is considered a duplicate if two conditions are satisfied:

1.  The two addresses normalize to the same (or similar) string using libpostal

2.  The two addresses are geographically within 1 kilometer of each other


<a id="org5ecfad3"></a>

## Diff Operation (from and address-based representation)

The diff operation is intended primarily for visualization purposes.


<a id="org788216f"></a>

### If the intersection between the two regions is greater than half of the size of either region, then the the two regions are considered to be the same.

The difference is the [symmetric difference](https://shapely.readthedocs.io/en/latest/manual.html#object.symmetric_difference) between the two regions.


<a id="org0a37281"></a>

### If not, the intersection of the two regions is the difference.


<a id="org7725db1"></a>

### If one of the regions completely contains the other, the symmetric difference is used.


<a id="org42a16ef"></a>

## Diff Operation (from a polygon representation)


<a id="org5912123"></a>

### The diff between two shapefiles are calculated by first converting to an address-based representation, then utilizing the previously defined diff operation on the address-based representation.


<a id="orgb7649b9"></a>

## Voronoi Diagram

In order to visualize an address-based representation of districts better, a voronoi diagram is used to create a polygon representation of the geographical region.

