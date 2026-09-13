# Design notes

## Primary failure mode addressed

Accessibility datasets are incomplete. Treating a missing curb, slope, width or surface value as "no barrier" creates false confidence. CurbShade instead adds an uncertainty term to the routing cost.

## Barrier vs preference

Some attributes are hard constraints, for example a curb above a profile's limit. Others are preferences: distance, heat exposure, crossing risk and uncertainty. The distinction is deliberate: a 2% longer route is negotiable; a non-traversable curb may not be.

## Thermal term

The current thermal term is intentionally simple:

`exposed_length = length * (1 - shade_fraction)`

and the route cost scales exposed length by a caller-supplied heat intensity in `[0, 1]`.

This is not a physiological model. A deployable system should incorporate weather, solar geometry, radiant temperature and user-specific needs.

## Compatibility

CurbShade uses a small normalized internal graph. `CurbShade-data` owns conversion from OSM / OpenSidewalks-like inputs. This isolates data licensing and schema churn from the routing engine.
