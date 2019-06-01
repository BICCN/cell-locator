---
name: QA checklist
about: Create checklist for testing the application
title: 'YYYY-MM-DD QA'
labels: 'qa: kitware, Category: Tests'

---

# Checklist

_Click_ means _Left-Click_

## Data, Units and default values

* [ ] Start application, and check:
* [ ] Atlas and ontology are loaded
* [ ] Unit displayed in Annotation Thickness, Slice Step Size and Slice offset boxes is `um`
* [ ] Exploration mode is selected
* [ ] Structure ontology is selected
* [ ] Slice Step Size is `25`
* [ ] Reset button is enabled
* [ ] Apply button is disabled
* [ ] Annotation Thickness slider is disabled
* [ ] Annotation Type is Spline
* [ ] Filename text box is `None`
* [ ] Coronal reference view is selected 

## Ontology combo box

_located in the lower left corner_

* [ ] Check that Ontology is visible in 2D and 3D views
* [ ] Select Layer -> Check that 2D and 3D views are updated
* [ ] Select None  -> idem

## DataProbe

_located in status bar, right of Ontology combo box_

* [ ] Mouse over slice in 2D view -> Confirm coordinate and structure name are displayed
* [ ] Select Layer ontology -> Mouse over slice in 2D view -> Check that layer name are displayed

## Contrast slider

* [ ] Select None in ontology combo box
* [ ] Click in between min/max and hold -> move mouse to translate range -> Check that 2D and 3D views are updated
* [ ] Click on handle min handle -> move mouse -> max handle should be symmetrically updated -> Check that 2D and 3D views are updated
* [ ] Click Reset button -> Check min/max are set ->  Check that 2D and 3D views are updated

## ReferenceView combo box

* [ ] Select Axial    -> 2D and 3D views are updated and have same orientation
* [ ] Select Sagittal -> idem
* [ ] Select Coronal  -> idem

## "Adjust Slice Viewer FOV" button

_located on the left of the Reference View combo box_

* [ ] Select "Coronal"  -> Move slider -> Click on button -> expected offset is  `6600` -> 2D and 3D views are updated
* [ ] Select "Axial"    -> idem                                                 `-3975` -> idem
* [ ] Select "Sagittal" -> idem                                                  `5699` -> idem

## Slice offset slider

* [ ] Move Slider -> check that TextBox, 2D and 3D views are updated
* [ ] Use mouse wheel in 2D view -> check that Slider, TextBox, 2D and 3D views are updated
* [ ] Enter value in TextBox -> check that Slider, 2D and 3D view are updated.
      **Known issues**: [#73](https://github.com/BICCN/cell-locator/issues/73)

## Slice Step Size slider

* [ ] Set Slice Step Size to `5`
* 2D view
  * [ ] Click once on 2D view -> use right&left arrow -> check slice offset is updated by `5` increment in 2D and 3D views updated
  * [ ] Click once on 2D view -> move mouse cursor outside of 2D view -> use right&left arrow -> idem
*  3D view
  * [ ] Click once on 3D view slice plane -> use right&left arrow -> check slice offset is updated by `5` increment, 2D and 3D views updated. 
        **Known issues:** [#83](https://github.com/BICCN/cell-locator/issues/83)
  * [ ] Click once on 3D view slice plane -> move mouse cursor outside slice plane -> use right&left arrow -> nothing happen.
        **Known issues:** [#84](https://github.com/BICCN/cell-locator/issues/84)
  * [ ] Use mouse wheel to zoom in until no background is visible -> move mouse cursor outside -> use right&left arrow -> check slice offset updated by `5` increment in 2D and 3D views updated.
        **Known issues:** [#83](https://github.com/BICCN/cell-locator/issues/83)

## Roll/Pitch/Yaw sliders

* [ ] Move Roll, Pitch and Yaw sliders -> Apply button is enabled -> wait few seconds, no update should happen -> click Apply -> 2D and 3D views should be updated
* [ ] Click Reset -> Raw/Pitch/Yaw reset to 0 -> Apply button disabled, slice offset set to `6600`
* [ ] Update Roll, Pitch, Yaw spin boxes with 25, 35 and 50 -> wait few seconds, nothing should happen -> click Apply -> 2D and 3D views should be updated, slice offset is set to `9478.087`
* [ ] Click Reset
* [ ] Move Roll slider  -> wait few seconds, no update should happen -> press Enter or Return -> 2D and 3D views should be updated
* [ ] Move Pitch slider -> idem
* [ ] Move Yaw slider   -> idem
* [ ] Update Roll spin box  -> wait few seconds, no update should happen -> press Enter or Return -> 2D and 3D views should be updated
* [ ] Update Pitch spin box -> idem
* [ ] Update Yaw spin box   -> idem

## 3D View

* [ ] Click and hold outside slice plane + move mouse cursor -> camera is updated
* [ ] Click and hold on slice plane + move mouse cursor -> slice offset is updated
* [ ] Click and hold on slice plane red orthogonal arrow + move mouse cursor -> raw/pitch/yaw are updated, slice offset is updated -> Apply button is disabled

## Annotation creation and updates (Edit mode vs Exploration mode)

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

## Keyboard Accelerators and Mouse Operations

See https://github.com/BICCN/cell-locator#keyboard-accelerators-and-mouse-operations

* [ ] Check `General`
* [ ] Check `2D Viewer`
* [ ] Check `2D Viewer / Zoom and Pan`
* [ ] Check `2D Viewer / Annotation`
* [ ] Check `3D Viewer`
* [ ] Check `SpinBoxes and Sliders`

## Annotation Type

* [ ] Set Annotation Type to Spline
* [ ] Select Edit mode -> Create an annotation
* [ ] Select PolyLine -> Annotation type is updated in 2D and 3D views
* [ ] Add annotation point -> annotation type should remain the same

## Annotation Thickness

* [ ] Select Edit mode -> Annotation Thickness slider is still disabled
* [ ] Add an annotation point -> Annotation Thickness slider is enabled
* [ ] Add multiple point -> Update thickness -> 3D view annotation thickness is updated
* [ ] Select point -> Press Delete multiple times to delete all point -> Annotation Thickness slider is disabled

## Confirm Exit Dialog

* [ ] Start application -> Close application -> No confirmation dialog -> Application is closed
* [ ] Start application -> Update camera, update slice offset, reset FOV -> Close application -> No confirmation dialog -> Application is closed
* [ ] Start application -> Select Edit mode -> Add points
* [ ] Close application -> Confirmation dialog -> Click "Cancel exit" -> Nothing happen
* [ ] Close application -> Confirmation dialog -> Click "Save" -> Save Dialog show -> Click Cancel -> Application stays open
* [ ] Close application -> Confirmation dialog -> Click "Save" -> Save Dialog show -> Select location -> Click Save -> Application is closed
* [ ] Start application -> Select Edit mode -> Add points -> Close application -> Confirmation dialog -> Click "Exit (discard modification)" -> Exit without saving annotation -> Application is closed    

## Check current filename is displayed

* [ ] Click New -> Enter `annotation.json` -> Click Save
      -> Check that filename text box displays `/path/to/annotation.json`
* [ ] Click New  -> Enter `annotation2.json` -> Click Save
      -> Check that filename text box displays `/path/to/annotation2.json`
* [ ] Click Load -> Select `annotation.json` -> Click Load
      -> Check that filename text box displays `/path/to/annotation.json`
* [ ] Click SaveAs -> Enter `annotation3.json`-> Click Save
      -> Check that filename text box displays `/path/to/annotation3.json`

## Test Cancelling New/SaveAs/Load is a no-op

* [ ] Click New    -> Click Cancel -> Click Save -> Existing annotation should be saved without showing "Save As" dialog
* [ ] Click SaveAs -> idem
* [ ] Click Load   -> idem
* [ ] Click SaveAs -> Check that "Save As" dialog is shown
      **Known issues:** [#86](https://github.com/BICCN/cell-locator/issues/86)

## Test Save -> New -> Load -> Save

Create annotation:

* [ ] Start application -> Set ReferenceView to Sagittal
* [ ] Select Edit mode -> Add 3 points
* [ ] Set properties
  * Raw/Pitch/Yaw set to 10/20/30
  * Slice Step Size to 10
  * Annotation thickness to 60
  * Annotation Type to PolyLine
* [ ] Click Save -> popup -> Enter `annotation.json` -> Click Save

Then:

* [ ] Click New -> popup -> Enter `annotation2.json` -> Click Save -> Click Reset -> Set Reference View to Axial
* [ ] Click Load -> Check that properties match the one entered above
* [ ] CTRL + W -> Application state is reset -> Click Load -> Check that properties match the ones entered above
* [ ] Close Application -> no confirmation dialog expected
      -> Start application -> Click Load -> Check that properties match the ones entered above
      **Known issues:** [#87](https://github.com/BICCN/cell-locator/issues/87)
* [ ] Click SaveAs -> Enter `annotation3.json` -> Click Save
* [ ] Check that file `annotation.json` and `annotation3.json` are identical.
      **Known issues:** [#78](https://github.com/BICCN/cell-locator/issues/78)

## Remembering directory used for last saving

* [ ] Start application -> Click Save -> Choose a different directory -> Choose Save -> Close application
* [ ] Start application -> Click Save -> Check suggest directory is the one of previous step
* [ ] Start application -> Click Load -> idem
      **Known issues:** [#85](https://github.com/BICCN/cell-locator/issues/85)
