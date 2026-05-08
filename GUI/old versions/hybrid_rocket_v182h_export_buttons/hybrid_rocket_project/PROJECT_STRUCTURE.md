# PROJECT STRUCTURE

## Directory Layout

```
hybrid_rocket_project/
│
├── main.py                          # Entry point - run this file
│
├── config/                          # Configuration and constants
│   ├── __init__.py
│   └── constants.py                # Colors, fonts, window settings
│
├── core/                            # Business logic layer
│   ├── __init__.py
│   ├── controller.py               # ApplicationController - state management
│   ├── data_manager.py             # DataManager - CSV operations
│   ├── data_structures.py          # Data classes (Configuration, Optimization, Mission)
│   └── optimization_runner.py      # Background thread execution
│
├── gui/                             # User interface layer
│   ├── __init__.py
│   ├── main_window.py              # Main window and coordination
│   │
│   ├── pages/                      # Individual pages
│   │   ├── __init__.py
│   │   ├── configuration_page.py  # Configuration inputs
│   │   └── optimization_page.py   # Optimization parameters
│   │
│   └── components/                 # Reusable UI components
│       ├── __init__.py
│       └── input_field.py          # Standardized input fields
│
├── backend/                         # Computation modules
│   ├── __init__.py
│   └── optimization.py             # Optimization calculations (mock/real)
│
├── utils/                           # Utility functions
│   └── __init__.py
│
└── tests/                           # Unit tests
    └── __init__.py
```

## File Purposes

### Entry Point

**main.py** (20 lines)
- Application entry point
- Simply creates root window and starts GUI
- Run this to start the application

### Configuration Package

**config/constants.py**
- Application-wide constants
- Color scheme
- Fonts
- Window settings
- File type definitions

### Core Package (Business Logic)

**core/controller.py** - ApplicationController
- Manages all application state
- Coordinates between GUI and backend
- Validates data readiness
- Prepares inputs for simulations
- Handles save/load operations

**core/data_manager.py** - DataManager
- All CSV file operations
- Serialization/deserialization
- Configuration save/load
- Optimization save/load
- Results save

**core/data_structures.py**
- `ConfigurationData` dataclass
- `OptimizationData` dataclass
- `MissionData` dataclass (template for future)
- Clean data structures with type hints

**core/optimization_runner.py** - OptimizationRunner
- Runs simulations in background thread
- Prevents UI freezing
- Handles callbacks (success/error)
- Thread management

### GUI Package (User Interface)

**gui/main_window.py** - HybridRocketGUI
- Main window setup
- Header and sidebar
- Page navigation
- Button creation
- Action handlers (save, load, run)
- Dialog management
- Results display

**gui/pages/configuration_page.py** - ConfigurationPage
- Configuration input fields
- Geometry section
- Fuel properties section
- Nozzle section
- Fuel selection (template)

**gui/pages/optimization_page.py** - OptimizationPage
- Parameter ranges
- Operating conditions
- Clean layout

**gui/components/input_field.py**
- Reusable InputField class
- Helper function for quick field creation
- Consistent styling

### Backend Package

**backend/optimization.py**
- Currently: Mock implementation
- Replace with: Your real optimization module
- Contains `full_range_simulation()` function

## Module Dependencies

```
main.py
  └── gui.main_window.HybridRocketGUI
       ├── config.constants (colors, fonts)
       ├── core.controller.ApplicationController
       ├── core.optimization_runner.OptimizationRunner
       ├── gui.pages.configuration_page
       └── gui.pages.optimization_page
            └── gui.components.input_field

ApplicationController
  ├── core.data_manager.DataManager
  └── core.data_structures (ConfigurationData, OptimizationData)

OptimizationRunner
  └── backend.optimization (full_range_simulation)

DataManager
  └── core.data_structures
```

## Import Structure

### From main.py:
```python
from gui.main_window import HybridRocketGUI
```

### From gui/main_window.py:
```python
from config.constants import COLORS, FONTS, WINDOW_CONFIG, BUTTON_STYLE, FILE_TYPES
from core.controller import ApplicationController
from core.optimization_runner import OptimizationRunner
from gui.pages.configuration_page import create_configuration_page
from gui.pages.optimization_page import create_optimization_page
```

### From pages:
```python
from config.constants import COLORS, FONTS
from gui.components.input_field import create_input_field
```

### From controller:
```python
from core.data_structures import ConfigurationData, OptimizationData
from core.data_manager import DataManager
```

### From optimization_runner:
```python
from backend import optimization as opt_module
```

## Adding New Pages

To add a new page (e.g., Mission, Results, Analysis):

1. **Create the page file:**
   ```
   gui/pages/mission_page.py
   ```

2. **Update gui/pages/__init__.py:**
   ```python
   from .mission_page import create_mission_page, MissionPage
   ```

3. **Add navigation in gui/main_window.py:**
   ```python
   btn_mission = tk.Button(sidebar, text="Mission", ...)
   btn_mission.pack(fill=tk.X, padx=10, pady=5)
   ```

4. **Create show_mission_page() method:**
   ```python
   def show_mission_page(self):
       self.current_page = 'mission'
       self.clear_content()
       page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
       page_frame.pack(fill=tk.BOTH, expand=True)
       self.current_page_obj = create_mission_page(page_frame, self.inputs)
       self.create_mission_buttons()
   ```

## Adding New Data Fields

To add fields to existing pages:

1. **In the page file (e.g., configuration_page.py):**
   ```python
   create_input_field(section, "Section_FieldName", 
                     "Field Label:", self.inputs, default="value", row=X)
   ```

2. **Field automatically appears in:**
   - `self.inputs` dictionary
   - `collect_configuration_data()` method
   - Save/load operations

## Running the Application

```bash
# From project root directory
python main.py
```

Or:
```bash
cd hybrid_rocket_project
python main.py
```

## File Sizes (Approximate)

- main.py: ~15 lines
- config/constants.py: ~60 lines
- core/controller.py: ~170 lines
- core/data_manager.py: ~160 lines
- core/data_structures.py: ~50 lines
- core/optimization_runner.py: ~90 lines
- gui/main_window.py: ~450 lines
- gui/pages/configuration_page.py: ~120 lines
- gui/pages/optimization_page.py: ~90 lines
- gui/components/input_field.py: ~70 lines
- backend/optimization.py: ~65 lines

**Total: ~1,350 lines** (vs 5,000+ if kept in one file)

## Benefits of This Structure

1. **Maintainability**: Each file has clear purpose
2. **Scalability**: Easy to add new pages/features
3. **Testability**: Each module can be tested independently
4. **Readability**: Files are reasonably sized (50-450 lines)
5. **Collaboration**: Multiple developers can work simultaneously
6. **Reusability**: Components can be shared between pages

## Next Steps

1. Run the application to verify everything works
2. Add your missing fields from original code
3. Replace mock optimization with real backend
4. Add new pages as needed (Mission, Results, Analysis)
5. Add plotting capabilities
6. Expand functionality incrementally

---
Last Updated: 2024-01-25
