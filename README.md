CellLocator by Allen Institute
==============================

Manually align specimens to annotated 3D spaces

![CellLocator by Allen Institute](Applications/CellLocatorApp/Resources/Images/SplashScreen.png?raw=true)

## Known Issues

* Inserting point in a `Spline` annotation does not work reliably. Workaround by switch the annotation type
  to `PolyLine` and then inserting the point. See [#80](https://github.com/BICCN/cell-locator/issues/80)
* For Roll, pitch and yaw, the angle mappings differ from the coordinate system the lab uses. See [#81](https://github.com/BICCN/cell-locator/issues/81)

## Keyboard Accelerators and Mouse Operations

_On macOS use the Command key (⌘) instead of the Control (Ctrl) key_

### General

| Key      | Effect                                                  |
|----------|---------------------------------------------------------|
| Ctrl + n | Save if needed and create a new annotation              |
| Ctrl + s | Save current annotation                                 |
| Ctrl + w | Reset views discarding current changes                  |


### 2D Viewer

| Key                             | Effect                                                   |
|---------------------------------|----------------------------------------------------------|
| f                               | Increment Slice offset                                   |
| b                               | Decrement Slice offset                                   |
| r                               | Adjust field of view to match the extent of the atlas    |


#### Zoom and Pan (available in Exploration and Edit mode)

| Interface Device                | Zoom                             | Pan                       |
|---------------------------------|----------------------------------|---------------------------|
| 3-button mouse                  | Right-Click & vertical drag      | Middle-Click & drag       |
| 2-button mouse                  | Right-Click & vertical drag      | Shift+Left-Click & drag   |
| 1-button mouse                  | Ctrl+Left-Click & vertical drag  | Shift+Left-Click & drag   |
| Trackpad                        | two-fingers & vertical drag      | Shift+Left-Click & drag   |


#### Annotation (available in Edit mode)

| Key or mouse operation                  | Effect                                                  |
|-----------------------------------------|---------------------------------------------------------|
| Left-Click                              | Add annotation point                                    |
| Delete                                  | Delete currently selected annotation point              |
| Ctrl + Left-Click on annotation line    | Insert annotation point                                 |
| Left-Click near annotation line & drag  | Translate annotation                                    |
| Right-Click near annotation line & drag | Scale annotation                                        |



### 3D Viewer


| Key                             | Effect                                                   |
|---------------------------------|----------------------------------------------------------|
| f                               | Increment Slice offset                                   |
| b                               | Decrement Slice offset                                   |
| r                               | Adjust field of view to match the extent of the atlas    |
