# Coordinate Systems

## Atlases

The table below describes the coordinate systems of the [reference atlases](reference-atlases.md) distributed in Cell Locator.

| Reference atlas                               | Atlas Version | Coordinate System Dimenstions |
|-----------------------------------------------|---------------|-------------------------------|
| Allen Mouse Brain Common Coordinate Framework | 3             | PIR                           |
| Allen Human Reference Atlas - 3D              | 1.0.0         | RAS                           |

By convention, the coordinate system dimensions are the the following:

* PIR (Posterior Inferior Right):
  * `X` axis is `Anterior-to-Posterior`
  * `Y` axis is `Superior-to-Inferior`
  * `Z` axis is `Left-to-Right`.

* RAS (Right Anterior Superior):
  * `X` axis is `Left-to-Right`
  * `Y` axis is `Posterior-to-Anterior`
  * `Z` axis is `Inferior-to-Superior`

## Cell Locator

World space for 3D Views is in RAS (Right Anterior Superior) orientation where `x axis = Left-to-Right`, `y axis = Posterior-to-Anterior` and `z axis = Inferior-to-Superior`.

:::{admonition} CCF Atlas integration
:class: warning

Since the orientation header in the `.nrrd` files used for the CCF are incorrect[^1], Cell Locator workarounds the problem by applying two countermeasures:
1. It associates a `RAStoPIR` transform[^2] with both the loaded CCF average template and annotation volumes..
2. It updates the slice orientation preset associated with the coronal viewer[^3] so that `+x` is `+P`.
:::

[^1]: https://github.com/BICCN/cell-locator/issues/48
[^2]: https://github.com/BICCN/cell-locator/issues/48#issuecomment-443412860
[^3]: https://github.com/BICCN/cell-locator/issues/48#issuecomment-443423073
