# Coordinate Systems

## CCF Atlas

The common reference space is in PIR (Posterior Inferior Right) orientation where `x axis = Anterior-to-Posterior`, `y axis = Superior-to-Inferior` and `z axis = Left-to-Right`.

Cell Locator bundles version 3 (2017).

![](https://help.brain-map.org/download/attachments/5308472/3DOrientation.png?version=1&modificationDate=1368132564812&api=v2)

References:
* https://biccn.org/standards/common-coordinate-frameworks-biccn
* http://help.brain-map.org/display/mousebrain/API#API-DownloadAtlas3-DReferenceModels

## MNI Atlas

The common reference space is in RAS (Right Anterior Superior) orientation where `x axis = Left-to-Right`, `y axis = Posterior-to-Anterior` and `z axis = Inferior-to-Superior`.

Cell Locator bundles version `mni_icbm152_t1_tal_nlin_sym_09b_hires`.

References:
* https://nist.mni.mcgill.ca/icbm-152-nonlinear-atlases-2009/

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
