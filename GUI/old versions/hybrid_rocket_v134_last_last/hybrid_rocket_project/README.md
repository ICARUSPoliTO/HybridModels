# Hybrid Rocket Simulator - Modular Structure

A professional, modular Python application for hybrid rocket simulation with optimization capabilities.

## ⚡ Quick Start

### Windows
```batch
# Double-click run_windows.bat
# OR in command prompt:
cd hybrid_rocket_project
run_windows.bat
```

### Linux / Mac
```bash
cd hybrid_rocket_project
chmod +x run_linux_mac.sh
./run_linux_mac.sh
```

### Manual Installation
```bash
cd hybrid_rocket_project
pip install -r requirements.txt
python main.py
```

## 📦 Requirements

### Python Version
- Python 3.8 or higher

### Dependencies (auto-installed via requirements.txt)
| Package | Purpose |
|---------|---------|
| numpy | Numerical computation |
| scipy | Scientific computing |
| matplotlib | Plotting and visualization |
| CoolProp | Thermodynamic properties |
| rocketcea | NASA CEA interface |
| pandas | Data export |
| openpyxl | Excel file creation |

### Platform-Specific Notes

**Windows:**
- If RocketCEA fails to install, you need Visual Studio Build Tools with C++ compiler
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk  # Required for GUI
```

**Mac:**
```bash
brew install python-tk  # If tkinter is missing
```

## 📁 What's Included

- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Configuration Page** - Rocket parameters input
- ✅ **Optimization Page** - Parameter range optimization
- ✅ **Mission Simulation** - Full mission analysis
- ✅ **Gox Analysis** - Oxidizer mass flux visualization
- ✅ **Excel Export** - Export all results to Excel
- ✅ **Custom Geometry** - Import grain geometry from CSV
- ✅ **CSV Save/Load** - Persistent data storage
- ✅ **Background Threading** - No UI freezing

## 📚 Documentation

**Start Here:**
- 📖 **SETUP_GUIDE.md** - Detailed installation and usage
- 🏗️ **PROJECT_STRUCTURE.md** - Architecture overview
- 🚀 **MISSION_GUIDE.md** - Mission simulation guide
- 🤝 **WORKING_WITH_CLAUDE.md** - How to request changes

## 🎯 Features

### Optimization
- Full parameter range simulation
- Gox (oxidizer mass flux) filtering
- Interactive contour plots
- TOP 10 solutions ranking
- Excel export with all data

### Grain Geometry
- Preset shapes: Cylindrical, Star, Wagon Wheel, Regular Polygon
- Custom geometry import from CSV
- Visual preview

### Mission Simulation
- Match mission mode
- Full mission mode
- Time-resolved performance plots

## 🔧 Troubleshooting

### "No module named tkinter"
```bash
# Linux
sudo apt-get install python3-tk

# Mac
brew install python-tk
```

### "RocketCEA installation failed"
- Windows: Install Visual Studio Build Tools
- Try: `pip install rocketcea --only-binary :all:`

### "CoolProp installation failed"
```bash
pip install CoolProp --no-cache-dir
```
- NumPy
- Tkinter (included with Python)
- CoolProp (optional)

## 📦 Structure

```
hybrid_rocket_project/
├── main.py              # Run this!
├── config/             # Constants and settings
├── core/               # Business logic
├── gui/                # User interface
│   ├── pages/         # Individual pages
│   └── components/    # Reusable UI components
├── backend/           # Optimization calculations
└── tests/             # Unit tests
```

## 🚀 Usage

### Basic Workflow

1. **Configure** - Set rocket parameters
2. **Save** - Store configuration
3. **Optimize** - Set ranges and run
4. **Results** - View and export

### Example Session

```bash
# Start application
python main.py

# In GUI:
# 1. Fill configuration → Save → Send to Optimization
# 2. Fill optimization parameters → Run
# 3. View results → Save to CSV
```

## 🔨 Customization

### Add New Fields
Open relevant page file → Add field → Restart

### Add New Pages
Create page file → Update main_window.py → Restart

### Modify Colors
Edit `config/constants.py` → Restart

See **SETUP_GUIDE.md** for details.

## 🤝 Working with Claude

This structure is designed for easy collaboration with Claude AI:

- Tell me what you want
- I identify the right file
- I make precise changes
- You test and iterate

See **WORKING_WITH_CLAUDE.md** for tips.

## 📊 Architecture Highlights

**Separation of Concerns:**
- **GUI Layer** - User interface (gui/)
- **Core Layer** - Business logic (core/)
- **Backend Layer** - Computations (backend/)
- **Config Layer** - Settings (config/)

**Benefits:**
- Easy to maintain
- Easy to test
- Easy to extend
- Easy to understand

## 🧪 Testing

```bash
# Test imports
python -c "from gui.main_window import HybridRocketGUI; print('OK')"

# Run application
python main.py
```

## 📝 Adding Features

### Example: Add Mission Page

1. Create `gui/pages/mission_page.py`
2. Update `gui/main_window.py` with navigation
3. Add `MissionData` to `core/data_structures.py`
4. Implement save/load in `core/data_manager.py`

Detailed instructions in **SETUP_GUIDE.md**.

## 🐛 Troubleshooting

**App won't start:**
- Check Python version (3.7+)
- Verify NumPy is installed
- Check file structure is intact

**Fields not saving:**
- Verify field key naming
- Check console for errors
- Review collect_*_data() methods

See **SETUP_GUIDE.md** for more help.

## 📈 Roadmap

- [x] Core architecture
- [x] Configuration page
- [x] Optimization page
- [x] CSV persistence
- [x] Background threading
- [ ] Mission page (template ready)
- [ ] Results visualization
- [ ] Plot generation
- [ ] Batch processing
- [ ] Advanced analysis

## 🤝 Contributing

This is your project! Modify, extend, and build as needed.

Tips:
- Follow existing patterns
- Keep files focused and small
- Document new features
- Test after changes

## 📄 License

[Add your license here]

## 🙋 Support

For questions about:
- **Structure** - See PROJECT_STRUCTURE.md
- **Usage** - See SETUP_GUIDE.md
- **Working with Claude** - See WORKING_WITH_CLAUDE.md

## 🎓 Learning Resources

The code itself is the best resource:
- Clear naming conventions
- Comprehensive docstrings
- Logical organization
- Consistent patterns

Start with `main.py` and explore from there!

## ✨ Credits

Architecture designed for:
- Maintainability
- Scalability
- Collaboration
- Professional quality

Built with Python, Tkinter, and NumPy.

---

**Version:** 1.0  
**Last Updated:** 2024-01-25  
**Status:** Ready for development

🚀 Happy coding!
