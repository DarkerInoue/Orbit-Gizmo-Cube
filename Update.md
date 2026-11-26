# Update

## Unreleased 1.0.2
- The cube is now a bevelled cube (6 octagonal faces, 12 edge strips, 8 hexagonal corners).
- Clicking Front / Back / Left / Right / Top / Bottom now puts Blender in a real
  axis view (not "User Perspective"), so the grid and axes of that plane are drawn.
  New option Navigation > Orthographic on Axis Views (on by default). Rotating
  away from an axis view restores the previous projection.

## 1.0.1
- Viewport clip start / end now follow the zoom (Navigation > Auto Clip
  Distance), so mm / micrometre objects are no longer cut off when you zoom
  in, and large scenes do not vanish when you zoom out.
- Shift+A creates objects at their native size in the current unit (2 mm
  cube in mm, 2 m cube in m, 2 in cube in inches...). Blender's remembered
  "last used" sizes are reset whenever the unit changes (Units & Grid >
  Native Size for New Objects).

## 1.0.0
- Rewritten as modules (maths / layout / icons / drawing / gizmo / units).
- Toolbar buttons are drawn and hit-tested from one Layout instead of
  Blender button gizmos; icons are drawn by the add-on.
- Last toolbar button is now Perspective / Orthographic. The view is no
  longer forced to orthographic anywhere.
- Cells seen edge-on no longer take clicks meant for their neighbours.
- New Units & Grid panel: unit switch, grid cell size, converter.
