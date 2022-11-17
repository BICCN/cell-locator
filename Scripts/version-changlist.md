# Base

```diff
+ Locked
+ MarkupLabelFormat
+ Markups []
+ Markups_Count
+ TextList [null]
+ TextList_Count 0
```

# 2019-01-26 -> 2020-04-16

2020-04-16, 2020-04-30, and 2020-08-26 all use the same format.

```diff
+ DefaultCameraPosition
+ DefaultCameraViewUp
+ DefaultOntology
+ DefaultReferenceView
+ DefaultRepresentationType
+ DefaultSplineOrientation
+ DefaultStepSize
+ DefaultThickness
```

# 2020-04-16 -> 2020-08-26

Major Change

```diff
! DefaultCameraPosition      -> cameraPosition
! DefaultCameraViewUp        -> cameraViewUp
! DefaultOntology            -> ontology
! DefaultReferenceView       -> referenceView
! DefaultStepSize            -> stepSize 

- DefaultRepresentationType
- DefaultSplineOrientation
- DefaultThickness

- Locked
! MarkupLabelFormat -> markups[].markup.labelFormat 
- Markups_Count
- TextList
- TextList_Count

! Markups[] (each element):
!     OrientationWXYZ -> orientation
!     RepresentationType -> representationType
!     Thickness -> thickness

+     markup
+         type
+         coordinateSystem
+         locked
+         labelFormat
+         controlPoints []
+             id
+             label
+             description
+             associatedNodeID
+             position []
+             orientation []
+             selected
+             locked
+             visibility
+             positionStatus
+         display
+             <displaynode>
            
-     AssociatedNodeID
-     CameraPosition
-     CameraViewUp
-     Closed
-     Description
-     ID
-     Label
!     Locked -> markup.locked
-     Ontology
!     Points[][] -> markup.controlPoints[].position[]
-     Poinst_Count
-     ReferenceView
-     Selected
-     StepSize
-     Visibility
```

# 2020-08-26 -> 2020-09-18

```diff
! markups[]
+     name
!     markup
-         locked
-         labelFormat
-         display
!         controlPoints
-             associatedNodeID
-             description
-             label
-             locked
-             positionStatus
-             selected
-             visibility
```

# 2020-09-18 -> 2021-06-08

```diff
+ version
! markups[]
+     coordinateUnits
+     measurements []
+         name
+         enabled
+         printFormat
+         units?
```

# 2021-06-08 -> 2021-06-11

```diff
! markups[]
-     measurements
```
