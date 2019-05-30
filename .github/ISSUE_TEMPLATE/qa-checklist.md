---
name: QA checklist
about: Create checklist for testing the application
title: 'YYYY-MM-DD QA'
labels: 'qa: kitware, C: tests'

---

* Data, Data Probe, Units
  * [ ] Start application
  * [ ] Atlas and ontology are loaded
  * [ ] Unit displayed in Annotation Thickness spinbox, Slice Step Size spinbox and slice offset text box is `mm`

* Ontology combo box (located in the lower left corner)
  * [ ] Start application
  * [ ] Structure is selected by default
  * [ ] Ontology is expected to be visible in 2D and 3D views
  * [ ] Select Layer -> 2D and 3D views should be updated
  * [ ] Select None  -> idem

* ReferenceView combox box
  * [ ] Start application
  * [ ] Coronal is selected by default
  * [ ] Select Axial    -> 2D and 3D views are updated and have same orientation
  * [ ] Select Sagittal -> idem
  * [ ] Select Coronal  -> idem

* "Adjust Slice Viewer FOV" button  (located on the left of the Reference View combo box)
  * [ ] Start application
  * [ ] Select "Coronal"  -> Move slider -> Click on button -> expected offset is  `6600` -> 2D and 3D views are updated
  * [ ] Select "Axial"    -> idem                                                 `-3975` -> idem
  * [ ] Select "Sagittal" -> idem                                                  `5699` -> idem

* Slice offset
  * [ ] Start application
  * [ ] Move Slider -> check that TextBox, 2D and 3D views are updated
  * [ ] Use mouse wheel in 2D view -> check that Slider, TextBox, 2D and 3D views are updated
  * [ ] Enter value in TextBox -> check that Slider, 2D and 3D view are updated - **Known issues**: [#73](https://github.com/BICCN/cell-locator/issues/73)

* Slice step size
  * [ ] Start application
  * [ ] Slice Step Size is `1`
  * [ ] Update to `200`
  * 2D view
    * [ ] Click once on 2D view -> use right&left arrow -> slice offset updated by `200` increment, 2D and 3D views updated
    * [ ] Click once on 2D view -> move mouse cursor outside of 2D view -> use right&left arrow -> idem
  *  3D view
    * [ ] Click once on 3D view slice plane -> use right&left arrow -> slice offset updated by `200` increment, 2D and 3D views updated
    * [ ] Click once on 3D view slice plane -> move mouse cursor outside slice plane -> use right&left arrow -> camera is updated
    * [ ] use mouse wheel to zoom in until no background is visible -> move mouse cursor outside -> use right&left arrow -> slice offset updated by `200` increment, 2D and 3D views updated

* Roll/Pitch/Yaw
  * [ ] Start application
  * [ ] Reset button is enabled
  * [ ] Apply button is disabled
  * [ ] Move Roll, Pitch and Yaw sliders -> Apply button is enabled -> wait few seconds, no update should happen -> click Apply -> 2D and 3D views should be updated
  * [ ] Click Reset -> Raw/Pitch/Yaw reset to 0 -> Apply button disabled, slice offset set to `6600`
  * [ ] Update Roll, Pitch, Yaw spin boxes with 25, 35 and 50 -> wait few seconds, nothing should happen -> click Apply -> 2D and 3D views should be updated, slice offset is set to `9465.563`
  * [ ] Click Reset
  * [ ] Move Roll slider  -> wait few seconds, no update should happen -> press Enter or Return -> 2D and 3D views should be updated
  * [ ] Move Pitch slider -> idem
  * [ ] Move Yaw slider   -> idem
  * [ ] Update Roll spin box  -> wait few seconds, no update should happen -> press Enter or Return -> 2D and 3D views should be updated
  * [ ] Update Pitch spin box -> idem
  * [ ] Update Yaw spin box   -> idem

* 3D View
  * [ ] Start application
  * [ ] Click and hold outside slice plane + move mouse cursor -> camera is updated
  * [ ] Click and hold on slice plane + move mouse cursor -> slice offset is updated
  * [ ] Click and hold on slice plane red orthogonal arrow + move mouse cursor -> raw/pitch/yaw are updated, slice offset is updated -> Apply button is disabled

* Annotation creation and updates (Edit mode vs Exploration mode)
  * [ ] Start application
  * [ ] Exploration mode is selected
  * [ ] Select Edit mode -> Click on slice plane in 3D view -> nothing happen
  * [ ] Click once on 2D view -> Annotation point is added -> click multiple time -> annotation is created
  * [ ] Click and hold annotation point -> move mouse cursor -> point position is updated
  * [ ] Click and hold near annotation line and away of point -> move mouse cursor -> entire annotation is moved
  * Update slice offset
    * [ ] Using slider -> annotation position is updated
    * [ ] Using right&left arrow -> idem
    * [ ] Click and hold on image slice plane in 3D, move mouse -> idem
  * Update raw/pitch/yaw
    * [ ] Click and hold on slice plane red orthogonal arrow in 3D view + move mouse cursor -> annotation position is updated
    * [ ] Update Roll/Pitch/Yaw text boxes -> idem
  * [ ] Select Exploration mode -> annotation point or line can NOT be selected and translated
  * [ ] Select Edit mode -> annotation point or line can be updated

* Keyboard shortcuts
  * [ ] Create annotation -> add points -> select point -> Press Delete -> annotation point is removed

* Annotation Type
  * [ ] Start application
  * [ ] Annotation Type is Spline
  * [ ] Select Edit mode -> Create an annotation
  * [ ] Select PolyLine -> Annotation type is updated in 2D and 3D views
  * [ ] Add annotation point -> annotation type should remain the same

* Annotation Thickness
  * [ ] Start application
  * [ ] Annotation Thickness slider is disabled
  * [ ] Select Edit mode -> Annotation Thickness slider is still disabled
  * [ ] Add an annotation point -> Annotation Thickness slider is enabled
  * [ ] Add multiple point -> Update thickness -> 3D view annotation thickness is updated
  * [ ] Select point -> Press Delete multiple times to delete all point -> Annotation Thickness slider is disabled

