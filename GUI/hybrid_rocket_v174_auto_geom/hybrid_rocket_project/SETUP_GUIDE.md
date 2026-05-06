# SETUP AND USAGE GUIDE

## Quick Start (5 Minutes)

### Step 1: Get the Files

Download the entire `hybrid_rocket_project` folder to your computer.

### Step 2: Navigate to Project

```bash
cd path/to/hybrid_rocket_project
```

### Step 3: Run the Application

```bash
python main.py
```

That's it! The application should start.

## Full Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Required packages:
  ```bash
  pip install numpy
  ```

- Optional packages:
  ```bash
  pip install CoolProp  # For advanced oxidizer selection
  ```

### Installation

1. **Download the project folder**
   - Extract to a location on your computer
   - Keep the folder structure intact

2. **Verify structure:**
   ```bash
   hybrid_rocket_project/
   ├── main.py
   ├── config/
   ├── core/
   ├── gui/
   ├── backend/
   ├── utils/
   └── tests/
   ```

3. **Test the import structure:**
   ```bash
   cd hybrid_rocket_project
   python -c "from gui.main_window import HybridRocketGUI; print('Success!')"
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Usage Workflow

### First Time Running

1. **Start application:**
   ```bash
   python main.py
   ```

2. **Configuration page (default):**
   - Fill in geometry, fuel, and nozzle parameters
   - Click "Save Configuration" → choose filename (e.g., `config1.csv`)
   - Click "Send to Optimization"

3. **Navigate to Optimization page:**
   - Click "Optimization" in sidebar
   - Fill in parameter ranges
   - Fill in operating conditions
   - Click "Save Optimization Parameters" → choose filename (e.g., `optim1.csv`)

4. **Run simulation:**
   - Click "Run Optimization"
   - Wait for completion (~2 seconds with mock)
   - View results in popup
   - Save results if desired

### Subsequent Usage

**Load previous configuration:**
1. Start application
2. Click "Load Configuration"
3. Select your saved CSV file
4. Fields populate automatically

**Run different optimization:**
1. Go to Optimization page
2. Change parameters
3. Click "Run Optimization"

## Working with the Modular Structure

### Making Changes to UI

**To modify Configuration page:**
1. Open `gui/pages/configuration_page.py`
2. Find the section you want to modify (e.g., `create_fuel_section`)
3. Add/modify fields using `create_input_field()`
4. Save file
5. Restart application

**To modify Optimization page:**
1. Open `gui/pages/optimization_page.py`
2. Modify sections as needed
3. Save and restart

**To change colors/fonts:**
1. Open `config/constants.py`
2. Modify `COLORS` or `FONTS` dictionaries
3. Save and restart

### Adding New Features

**To add a new input field:**
```python
# In any page file
create_input_field(
    section, 
    "Section_FieldName",  # Key for accessing value
    "Field Label:",       # Display label
    self.inputs,          # Storage dictionary
    default="0.0",        # Default value
    row=0                 # Grid row position
)
```

**To add a new section:**
```python
def create_my_section(self, parent):
    section = tk.LabelFrame(
        parent, 
        text="My Section", 
        font=FONTS['section'],
        bg=COLORS['bg_medium'], 
        fg=COLORS['text_color']
    )
    section.pack(fill=tk.X, padx=20, pady=10)
    
    # Add fields to section
    create_input_field(section, ..., row=0)
    create_input_field(section, ..., row=1)
```

### Adding New Pages

1. **Create new page file:**
   ```bash
   # In gui/pages/
   touch mission_page.py
   ```

2. **Use template from configuration_page.py:**
   ```python
   class MissionPage:
       def __init__(self, parent, inputs_dict):
           self.parent = parent
           self.inputs = inputs_dict
           self.create_page()
       
       def create_page(self):
           # Your page content here
           pass
   ```

3. **Add to main_window.py:**
   ```python
   # Import
   from gui.pages.mission_page import create_mission_page
   
   # Create show method
   def show_mission_page(self):
       self.current_page = 'mission'
       self.clear_content()
       page_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
       page_frame.pack(fill=tk.BOTH, expand=True)
       self.current_page_obj = create_mission_page(page_frame, self.inputs)
       self.create_mission_buttons()
   
   # Add to sidebar in create_sidebar()
   btn_mission = tk.Button(
       sidebar, text="Mission",
       command=self.show_mission_page,
       ...
   )
   btn_mission.pack(fill=tk.X, padx=10, pady=5)
   ```

4. **Create button handler:**
   ```python
   def create_mission_buttons(self):
       button_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
       button_frame.pack(side=tk.BOTTOM, pady=20)
       
       tk.Button(button_frame, text="Save Mission", 
                command=self.save_mission, ...).pack(side=tk.LEFT, padx=10)
   ```

## Debugging

### Application won't start

**Check import errors:**
```bash
python -c "from gui.main_window import HybridRocketGUI"
```

**Check all packages are installed:**
```bash
python -c "import tkinter, numpy; print('OK')"
```

**Check file structure:**
```bash
ls -la hybrid_rocket_project/
ls -la hybrid_rocket_project/gui/pages/
```

### Fields not saving

1. Check that field key is correct
2. Verify `collect_configuration_data()` includes your fields
3. Check console for error messages

### Backend not working

1. Verify `backend/optimization.py` exists
2. Check imports:
   ```bash
   python -c "from backend import optimization; print('OK')"
   ```
3. Test backend independently:
   ```bash
   cd backend
   python optimization.py
   ```

## Development Workflow

### Recommended Process

1. **Make changes in one file at a time**
2. **Test after each change**
3. **Use print statements to debug:**
   ```python
   print(f"Field value: {self.inputs['MyField'].get()}")
   ```

4. **Check console output for errors**

### Version Control (Optional but Recommended)

```bash
cd hybrid_rocket_project
git init
git add .
git commit -m "Initial modular structure"
```

After changes:
```bash
git status
git diff  # See what changed
git add .
git commit -m "Description of changes"
```

## Common Tasks

### Change Default Values

Open relevant page file and modify `default` parameter:
```python
create_input_field(..., default="NEW_VALUE", ...)
```

### Add Validation

In `gui/main_window.py`, modify `collect_*_data()` methods:
```python
def collect_configuration_data(self):
    # ... existing code ...
    
    # Add validation
    value = self.inputs['MyField'].get()
    if not self.validate_my_field(value):
        messagebox.showerror("Error", "Invalid value")
        return None
    
    # ... rest of code ...
```

### Add New Data Type

1. Add to `core/data_structures.py`:
   ```python
   @dataclass
   class MissionData:
       burn_time: float
       altitude: float
       # ... other fields
   ```

2. Add to DataManager for save/load
3. Add to Controller for state management

## Tips for Success

1. **Start small**: Modify one thing at a time
2. **Test frequently**: Run after each change
3. **Read the code**: Each file has clear structure
4. **Follow patterns**: Use existing code as templates
5. **Ask for help**: If stuck, come back with specific file/line

## File Navigation Tips

**Quick reference for where things are:**

- **Colors**: `config/constants.py` → `COLORS`
- **Fonts**: `config/constants.py` → `FONTS`
- **Add field**: Relevant page file → `create_*_section()`
- **Save logic**: `core/data_manager.py` → `save_*_csv()`
- **Backend call**: `core/optimization_runner.py` → `run_simulation()`
- **Button handlers**: `gui/main_window.py` → `save_*()`, `load_*()`, etc.

## Performance Tips

- **Mock backend**: Fast for UI development (~2 seconds)
- **Real backend**: May take minutes for large parameter spaces
- **Start small**: Use 3-5 points for testing, increase later

## Next Steps

1. ✅ Verify application runs
2. ✅ Test save/load functionality
3. ✅ Run mock optimization
4. 📝 Add your missing fields
5. 📝 Replace mock with real backend
6. 📝 Add new pages (Mission, Results)
7. 📝 Add plotting capabilities
8. 📝 Expand as needed

---
Last Updated: 2024-01-25
