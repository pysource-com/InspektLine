# InspektLine GUI Architecture

## Visual Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     InspektLine Application                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   main.py       │ ◄─── New Entry Point
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   gui.py        │ ◄─── Compatibility Wrapper
                    └─────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │         gui/ Package                       │
        └───────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ components/ │     │   pages/    │     │  styles/    │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                     │
        │                   │                     │
┌───────┴───────┐   ┌───────┴───────┐   ┌────────┴────────┐
│               │   │               │   │                 │
▼               ▼   ▼               ▼   ▼                 ▼
SidebarButton  Video  Camera      Dataset  DarkTheme  StyleSheets
               Label  Page        Page
                      Settings
                      Page
```

## Module Relationships

```
main_window.py
    │
    ├─► components/
    │       ├─► SidebarButton  (navigation)
    │       └─► VideoLabel     (video display)
    │
    ├─► pages/
    │       ├─► CameraPage     (uses VideoLabel, StyleSheets)
    │       ├─► DatasetPage    (uses VideoLabel, StyleSheets)
    │       └─► SettingsPage   (uses StyleSheets)
    │
    └─► styles/
            ├─► DarkTheme      (color definitions)
            └─► StyleSheets    (reusable styles)
```

## Data Flow

```
┌──────────────┐
│   Camera     │ ◄───── camera.Camera (external)
│   Hardware   │
└──────┬───────┘
       │
       │ frames
       ▼
┌──────────────┐
│ MainWindow   │
│  (manages    │
│   camera)    │
└──────┬───────┘
       │
       ├─► VideoLabel (CameraPage)    ─► Display
       │
       └─► VideoLabel (DatasetPage)   ─► Display
```

## Page Navigation Flow

```
                    ┌─────────────────┐
                    │  MainWindow     │
                    │  Sidebar        │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐   ┌───────────────┐
│  CameraPage   │    │ DatasetPage   │   │ SettingsPage  │
│               │    │               │   │               │
│  [Video]      │    │  [Video]      │   │  [Config]     │
│  [Controls]   │    │  [Stats]      │   │  [Camera]     │
│               │    │  [Buttons]    │   │  [Detection]  │
└───────────────┘    └───────────────┘   └───────────────┘
     Index: 0             Index: 1             Index: 2
```

## Component Hierarchy

```
MainWindow (QMainWindow)
    │
    ├─► Sidebar (QFrame)
    │       └─► SidebarButton × 7
    │
    └─► QStackedWidget
            │
            ├─► CameraPage (QWidget)
            │       ├─► Header
            │       ├─► VideoLabel
            │       └─► ControlPanel
            │               ├─► Sliders
            │               └─► Buttons
            │
            ├─► DatasetPage (QWidget)
            │       ├─► Header
            │       ├─► LeftPanel
            │       │       ├─► Statistics
            │       │       ├─► DefectCategory
            │       │       └─► RecentSamples
            │       ├─► CenterPanel
            │       │       ├─► VideoLabel
            │       │       └─► CaptureButtons
            │       └─► RightPanel
            │               └─► Gallery
            │
            └─► SettingsPage (QWidget)
                    ├─► LeftMenu
                    └─► ScrollArea
                            ├─► CameraConfig
                            └─► DetectionParams
```

## Styling Architecture

```
┌──────────────────────┐
│    DarkTheme         │ ◄─── Color Palette
│                      │
│  BG_PRIMARY          │
│  BG_SECONDARY        │
│  TEXT_PRIMARY        │
│  PRIMARY             │
│  SUCCESS / ERROR     │
│  ...                 │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   StyleSheets        │ ◄─── Reusable Styles
│                      │
│  get_icon_button()   │
│  get_slider()        │
│  get_combobox()      │
│  get_checkbox()      │
│  get_input()         │
└──────────┬───────────┘
           │
           ▼
    ┌──────┴──────┐
    │   Applied   │
    │     to      │
    │  Components │
    └─────────────┘
```

## State Management

```
┌─────────────────────────────────────────┐
│          MainWindow State                │
├─────────────────────────────────────────┤
│  Camera State:                           │
│    - camera_index                        │
│    - camera_type                         │
│    - cap (VideoCapture)                  │
│    - timer                               │
│                                          │
│  UI State:                               │
│    - is_inspecting                       │
│    - exposure_value                      │
│    - contrast_value                      │
│                                          │
│  Dataset State:                          │
│    - is_capturing                        │
│    - total_samples                       │
│    - ok_samples                          │
│    - not_ok_samples                      │
└─────────────────────────────────────────┘
           │
           ├─► Shared with Pages
           │
           └─► Updated by User Actions
```

## Event Flow

```
User Action
    │
    ▼
Sidebar Button Click
    │
    ▼
MainWindow.switch_page()
    │
    ├─► Update QStackedWidget
    ├─► Update Button States
    └─► Enable/Disable Page Features
            │
            ▼
        Page Displayed
```

## Camera Update Loop

```
┌─────────────────┐
│   QTimer        │
│   (30ms)        │
└────────┬────────┘
         │
         ▼
MainWindow.update_frame()
         │
         ├─► camera.read_frame()
         │       │
         │       ▼
         │   [frame data]
         │
         ├─► CameraPage.video_label.display_frame()
         │
         └─► DatasetPage.video_label.display_frame()
```

## File Size Distribution

```
Components (90 lines)
├─► sidebar_button.py    35 lines
└─► video_label.py       55 lines

Pages (1,060 lines)
├─► camera_page.py      260 lines
├─► dataset_page.py     450 lines
└─► settings_page.py    350 lines

Styles (205 lines)
├─► themes.py            65 lines
└─► stylesheets.py      140 lines

Core (350 lines)
└─► main_window.py      350 lines

Total: ~1,705 lines across 8 modules
```

## Import Dependencies

```
main.py
    └─► gui.MainWindow

gui/__init__.py
    └─► main_window.MainWindow

main_window.py
    ├─► camera.camera.Camera
    ├─► gui.components.SidebarButton
    ├─► gui.pages.*
    └─► gui.styles.DarkTheme

pages/*.py
    ├─► gui.components.*
    └─► gui.styles.*

components/*.py
    └─► PySide6.*

styles/*.py
    └─► (no internal dependencies)
```

## Comparison: Before vs After

### Before (Monolithic)
```
gui.py (1,527 lines)
    └─► Everything in one file
        - Hard to navigate
        - Difficult to test
        - Tight coupling
```

### After (Modular)
```
gui/
├─► main_window.py       (navigation & state)
├─► components/          (reusable widgets)
│   ├─► sidebar_button
│   └─► video_label
├─► pages/               (feature pages)
│   ├─► camera_page
│   ├─► dataset_page
│   └─► settings_page
└─► styles/              (theming)
    ├─► themes
    └─► stylesheets

Benefits:
✓ Easy to navigate
✓ Simple to test
✓ Loose coupling
✓ Clear responsibilities
```

## Extension Points

Want to add new functionality? Here's where:

### New Page
```
gui/pages/analytics_page.py
    └─► Register in pages/__init__.py
        └─► Add to MainWindow.init_ui()
```

### New Component
```
gui/components/custom_chart.py
    └─► Register in components/__init__.py
        └─► Import in pages
```

### New Theme
```
gui/styles/themes.py
    └─► Add LightTheme class
        └─► Export in styles/__init__.py
```

### New Style
```
gui/styles/stylesheets.py
    └─► Add get_card_style() method
        └─► Use in pages
```

## Best Practices Applied

✅ **Single Responsibility Principle**
   - Each file has one clear purpose

✅ **Don't Repeat Yourself (DRY)**
   - Styles defined once, reused everywhere

✅ **Separation of Concerns**
   - UI, logic, and styling separated

✅ **Open/Closed Principle**
   - Easy to extend, no need to modify existing

✅ **Dependency Injection**
   - Pages receive parent window reference

✅ **Composition over Inheritance**
   - Components composed into pages

## Summary

The new architecture provides:
- **Modularity**: Clear separation of concerns
- **Maintainability**: Easy to find and fix issues
- **Scalability**: Simple to add new features
- **Testability**: Components can be tested independently
- **Readability**: Smaller, focused files
- **Reusability**: Components shared across pages

