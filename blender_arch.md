# Blender System Architecture

**Version:** 4.x  
**Last Updated:** March 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Build System](#3-build-system)
4. [Core Modules](#4-core-modules)
5. [Internal Libraries](#5-internal-libraries)
6. [External Dependencies](#6-external-dependencies)
7. [Python Integration](#7-python-integration)
8. [Architectural Patterns](#8-architectural-patterns)
9. [Programming Languages](#9-programming-languages)
10. [Key Design Decisions](#10-key-design-decisions)
11. [Testing Infrastructure](#11-testing-infrastructure)
12. [Documentation](#12-documentation)

---

## 1. Overview

Blender is a comprehensive open-source 3D creation suite featuring:

- **~2 million lines of code** (C/C++/Python)
- **100+ modules** in the source tree
- **30+ internal libraries**
- **30+ external dependencies**
- **Cross-platform** support (Windows, macOS, Linux)
- **Multi-backend rendering** (OpenGL, Vulkan, Metal)

### Core Architectural Principles

- **Modularity** - Clear separation of concerns
- **Portability** - Platform abstraction layers
- **Performance** - Parallel evaluation, GPU acceleration
- **Extensibility** - Python API, addon system
- **Compatibility** - DNA/RNA versioning system
- **Maintainability** - Comprehensive testing and documentation

---

## 2. Project Structure

```
blender/
├── source/              # Main source code
├── intern/              # Internal libraries (Blender-specific)
├── extern/              # External/third-party libraries
├── scripts/             # Python scripts and addons
├── release/             # Release packaging files
├── doc/                 # Documentation
├── tests/               # Test suites
├── tools/               # Development tools
├── build_files/         # Build system configuration
├── lib/                 # Pre-compiled libraries
├── assets/              # Asset files (brushes, nodes)
├── locale/              # Internationalization files
├── CMakeLists.txt       # Main CMake configuration
├── GNUmakefile          # Makefile convenience wrapper
└── pyproject.toml       # Python project configuration
```

### Directory Responsibilities

| Directory | Purpose |
|-----------|---------|
| **source/** | Core Blender application source code |
| **intern/** | Internal libraries (GHOST, Cycles, etc.) |
| **extern/** | Third-party libraries bundled with Blender |
| **scripts/** | Python scripts, modules, and addons |
| **release/** | Platform-specific packaging and data files |
| **build_files/** | CMake configuration and build scripts |
| **lib/** | Pre-compiled dependency libraries per platform |
| **doc/** | Documentation generation (Sphinx, Doxygen) |
| **tests/** | Unit tests, integration tests, benchmarks |
| **tools/** | Development and maintenance utilities |

---

## 3. Build System

### CMake-Based Build

**Primary Build File:** `CMakeLists.txt` (2956 lines)

**Requirements:**
- **CMake:** 3.10+
- **GCC:** 14.0.0+
- **Clang:** 17.0+
- **MSVC:** 2019 (1928)+
- **Out-of-source builds required**

### Build Configurations

| Configuration | Purpose |
|--------------|---------|
| `blender_release.cmake` | Full release build with all features |
| `blender_developer.cmake` | Developer build with debugging |
| `blender_lite.cmake` | Minimal build |
| `blender_full.cmake` | All features enabled |
| `blender_headless.cmake` | Server/renderfarm build |
| `bpy_module.cmake` | Python module build |
| `cycles_standalone.cmake` | Cycles renderer only |

### GNUmakefile Targets

```bash
make debug       # Debug build
make release     # Full release build
make lite        # Minimal build
make developer   # Developer build
make bpy         # Python module build
make cycles      # Cycles standalone
make ninja       # Use Ninja build system
make ccache      # Enable ccache
```

### Key Build Options

**Core Features:**
- `WITH_BLENDER` - Build main application
- `WITH_PYTHON` - Embedded Python API
- `WITH_INTERNATIONAL` - I18N support
- `WITH_BUILDINFO` - Build details in binary

**Rendering:**
- `WITH_CYCLES` - Cycles render engine
- `WITH_CYCLES_OSL` - OpenShadingLanguage support
- `WITH_CYCLES_EMBREE` - Embree ray tracing
- `WITH_HYDRA` - Hydra render engine
- `WITH_OPENIMAGEDENOISE` - AI denoising

**Simulation:**
- `WITH_BULLET` - Physics engine
- `WITH_MOD_FLUID` - Mantaflow fluid simulation
- `WITH_MOD_OCEANSIM` - Ocean simulation
- `WITH_MOD_REMESH` - Remesh modifier

**File Formats:**
- `WITH_ALEMBIC` - Alembic support
- `WITH_USD` - Universal Scene Description
- `WITH_IMAGE_OPENEXR` - OpenEXR images
- `WITH_CODEC_FFMPEG` - FFmpeg video

---

## 4. Core Modules

### Source Directory Structure

```
source/
├── creator/             # Application entry point
└── blender/             # Main Blender codebase
    ├── blenlib/         # Core library (data structures, math)
    ├── blenkernel/      # Core kernel (data-block management)
    ├── makesdna/        # DNA serialization system
    ├── makesrna/        # RNA reflection system
    ├── blenloader/      # .blend file I/O
    ├── windowmanager/   # Window and event management
    ├── editors/         # Editor implementations
    ├── gpu/             # GPU abstraction layer
    ├── draw/            # Drawing engines
    ├── render/          # Render pipeline
    ├── depsgraph/       # Dependency graph
    ├── nodes/           # Node system
    ├── geometry/        # Geometry processing
    ├── simulation/      # Simulation framework
    ├── compositor/      # Compositor
    ├── animrig/         # Animation rigging
    ├── asset_system/    # Asset management
    ├── python/          # Python API bindings
    ├── bmesh/           # Boundary mesh structure
    ├── imbuf/           # Image buffer handling
    ├── functions/       # Function system (Geometry Nodes)
    └── io/              # Import/Export formats
```

### Module Descriptions

#### creator/ - Application Entry Point
- Main application initialization
- Command-line argument parsing
- Signal handling and crash protection
- Subsystem initialization sequence

#### blenlib/ (BLI) - Core Library
**Purpose:** Foundation library providing:
- Data structures (lists, arrays, maps, sets, spans)
- Mathematical operations (vectors, matrices, quaternions)
- Memory management (pools, arenas)
- Threading and task system
- File operations and string utilities
- Hashing and randomization
- SIMD utilities

**Key Headers:**
- `BLI_listbase.h` - Linked list foundation
- `BLI_array.hh` - Dynamic arrays
- `BLI_map.hh`, `BLI_set.hh` - Associative containers
- `BLI_span.hh` - Non-owning view
- `BLI_math_vector.hh`, `BLI_math_matrix.hh` - Math types
- `BLI_task.hh` - Parallel task system

#### blenkernel/ (BKE) - Core Kernel
**Purpose:** Data-block management and business logic

**Key Responsibilities:**
- Main database management (`Main` struct)
- ID data-block operations
- Modifier and constraint systems
- Object/Scene/Collection management
- Mesh/Curve/Volume data handling
- Material and texture system
- Particle and animation data

**Key Headers:**
- `BKE_main.hh` - Main database struct
- `BKE_object.hh` - Object management
- `BKE_scene.hh` - Scene management
- `BKE_collection.hh` - Collection system
- `BKE_mesh.hh` - Mesh data handling
- `BKE_modifier.hh` - Modifier system
- `BKE_node.hh` - Node tree management

#### makesdna/ - DNA Serialization System
**Purpose:** Binary serialization format for .blend files

**Key Components:**
- DNA type definitions (`DNA_*_types.h`)
- SDNA (Struct DNA) chunk format
- Versioning and compatibility
- Endianness handling

**DNA Files:** 90+ type definition files including:
- `DNA_object_types.h` - Object data
- `DNA_mesh_types.h` - Mesh data
- `DNA_scene_types.h` - Scene data
- `DNA_node_types.h` - Node trees
- `DNA_userdef_types.h` - User preferences

#### makesrna/ (RNA) - Reflection System
**Purpose:** Runtime type information and property access

**Key Components:**
- `RNA_types.hh` - Type definitions
- `RNA_access.hh` - Property access API
- `RNA_define.hh` - Type registration

**Features:**
- Property introspection
- Python API binding foundation
- UI automatic generation
- Property path resolution
- Undo/redo support

#### blenloader/ (BLO) - File I/O
**Purpose:** .blend file reading/writing

**Key Files:**
- `BLO_readfile.hh` - File reading
- `BLO_writefile.hh` - File writing
- `BLO_undofile.hh` - Undo file handling
- `versioning_common.hh` - Version migration

#### windowmanager/ (WM) - Window Management
**Purpose:** Window, event, and tool management

**Key Components:**
- Window creation and management
- Event system (keyboard, mouse, etc.)
- Keymap system
- Tool and gizmo systems
- XR (VR/AR) support

#### editors/ - Editor Implementations

| Editor Directory | Purpose |
|-----------------|---------|
| `space_view3d/` | 3D Viewport |
| `space_image/` | Image Editor |
| `space_node/` | Node Editor |
| `space_outliner/` | Outliner |
| `space_graph/` | Graph Editor (F-Curves) |
| `space_action/` | Dope Sheet |
| `space_sequencer/` | Video Sequencer |
| `space_clip/` | Movie Clip Editor |
| `space_text/` | Text Editor |
| `space_console/` | Python Console |
| `space_file/` | File Browser |
| `space_buttons/` | Properties Editor |
| `sculpt_paint/` | Sculpt/Paint tools |
| `uvedit/` | UV Editor |
| `transform/` | Transform operations |

#### gpu/ - GPU Abstraction Layer
**Backends:** OpenGL, Vulkan, Metal

**Key Components:**
- Shader compilation and management
- Batch rendering
- Texture management
- Framebuffer management
- Compute shaders
- Immediate mode drawing

#### draw/ - Drawing Engines

| Engine | Purpose |
|--------|---------|
| `eevee/` | Real-time render engine |
| `workbench/` | Solid/viewport shading |
| `overlay/` | Overlay drawing (selection, guides) |
| `gpencil/` | Grease Pencil drawing |
| `select/` | Selection highlighting |
| `compositor/` | Compositor viewport |
| `external/` | External engine integration |

#### depsgraph/ - Dependency Graph
**Key Features:**
- Automatic dependency detection
- Parallel evaluation
- Animation/modifier/constraint evaluation

#### nodes/ - Node System
**Node Types:**
- `composite/` - Compositor nodes
- `shader/` - Shader nodes
- `geometry/` - Geometry Nodes
- `texture/` - Texture nodes
- `function/` - Function nodes

#### geometry/ - Geometry Processing
**Operations:**
- Mesh boolean operations
- Curve operations (resample, fillet, trim)
- Mesh primitives
- UV packing
- Point cloud and volume operations

#### compositor/ - Compositor
**Key Components:**
- Node operations
- Shader-based compositing
- Multi-threaded execution
- Domain-based processing

#### animrig/ - Animation Rigging
**Key Components:**
- Action and F-Curve management
- NLA (Non-Linear Animation)
- Bone collections
- Driver system and keyframing
- Pose management

#### asset_system/ - Asset Management
**Key Components:**
- Asset catalogs
- Asset libraries
- Asset representations
- Remote libraries

#### python/ - Python API
**Submodules:**
- `bpy/` - Main Python module
- `mathutils/` - Math types
- `gpu/` - GPU Python API
- `bmesh/` - BMesh Python API

#### bmesh/ - BMesh
**Purpose:** Boundary mesh data structure for edit-mode

**Features:**
- Topology operations
- Mesh tools and operators

#### imbuf/ - Image Buffer
**Key Components:**
- Image buffer management
- Color management (OpenColorIO)
- Image format support
- Thumbnail generation

#### render/ - Render Pipeline
**Key Components:**
- Render engine API
- Bake system
- Texture system
- Hydra integration

#### functions/ - Function System
**Purpose:** Generic function system (used by Geometry Nodes)

**Key Components:**
- Multi-function system
- Lazy function execution
- Field evaluation

#### io/ - Import/Export
**Formats Supported:**
- `alembic/` - Alembic (.abc)
- `fbx/` - FBX
- `usd/` - USD (.usd, .usda, .usdc)
- `wavefront_obj/` - OBJ
- `ply/` - PLY
- `stl/` - STL
- `grease_pencil/` - SVG, PDF
- `csv/` - CSV

---

## 5. Internal Libraries

**Location:** `intern/`

| Library | Purpose |
|---------|---------|
| **atomic/** | Atomic operations |
| **clog/** | C logging |
| **cycles/** | Cycles render engine |
| **dualcon/** | Dual contouring (remesh) |
| **eigen/** | Eigen math library |
| **ghost/** | GHOST windowing system |
| **guardedalloc/** | Memory debugging |
| **iksolver/** | Legacy IK solver |
| **itasc/** | ITASC IK solver |
| **libmv/** | Motion tracking |
| **mantaflow/** | Fluid simulation |
| **memutil/** | Memory utilities |
| **mikktspace/** | Tangent space |
| **opensubdiv/** | Subdivision surfaces |
| **openvdb/** | OpenVDB integration |
| **quadriflow/** | Quad remeshing |
| **rigidbody/** | Rigid body physics |
| **sky/** | Sky texture |
| **slim/** | SLIM UV unwrapping |

### GHOST (Generic Hardware Operating System Support)

**Purpose:** Cross-platform windowing and input system

**Platform Support:**
- Windows (Win32)
- macOS (Cocoa)
- Linux (X11, Wayland)
- Headless (None)
- SDL (fallback)

**Key Components:**
- Window management
- Event handling
- Context creation (OpenGL, Vulkan, Metal, D3D)
- Input devices (keyboard, mouse, tablet, NDOF)
- Drag and drop, IME, XR (OpenXR)

### Cycles Render Engine

**Architecture:**
```
cycles/
├── app/           # Standalone application
├── blender/       # Blender integration
├── bvh/           # BVH acceleration
├── device/        # Device backends
├── graph/         # Shader graph
├── hydra/         # Hydra delegate
├── integrator/    # Path tracing integrator
├── kernel/        # GPU/CPU kernels
├── scene/         # Scene representation
├── session/       # Render session
├── subd/          # Subdivision surfaces
├── test/          # Tests
└── util/          # Utilities
```

**Device Backends:**
- CPU (SSE4.2, AVX2, AVX512)
- CUDA (NVIDIA)
- OptiX (NVIDIA RTX)
- HIP (AMD)
- HIPRT (AMD Ray Tracing)
- Metal (Apple)
- oneAPI (Intel)

---

## 6. External Dependencies

**Location:** `extern/`

| Library | Purpose |
|---------|---------|
| **audaspace/** | Audio system |
| **binreloc/** | Binary relocation |
| **bullet2/** | Physics engine |
| **cuew/** | CUDA wrapper |
| **curve_fit_nd/** | Curve fitting |
| **draco/** | Mesh compression |
| **fast_float/** | Fast float parsing |
| **gflags/** | Command-line flags |
| **glew-es/** | OpenGL ES loader |
| **glog/** | Google logging |
| **gmock/, gtest/** | Testing framework |
| **hipew/** | HIP wrapper |
| **json/** | JSON parsing |
| **mantaflow/** | Fluid simulation |
| **nanosvg/** | SVG parsing |
| **quadriflow/** | Quad remeshing |
| **rangetree/** | Range tree data structure |
| **renderdoc/** | Graphics debugging |
| **tinygltf/** | glTF loader |
| **ufbx/** | FBX parsing |
| **vulkan_memory_allocator/** | Vulkan memory |
| **wcwidth/** | Character width |
| **wintab/** | Windows tablet |
| **xdnd/** | X11 drag-n-drop |
| **xxhash/** | Hashing |

### Dependency Chains

```
FFmpeg → zlib, openjpeg, x264, opus, vpx, theora, vorbis, ogg, lame, aom
OpenImageIO → png, zlib, openexr, jpeg, tiff, pugixml, fmt, openjpeg, webp
OpenColorIO → yamlcpp, expat, imath, pystring
OpenSubdiv → tbb
OpenVDB → tbb, zlib, blosc
OSL → LLVM, openexr, openimageio, pugixml
USD → tbb, opensubdiv
Embree → tbb
OpenImageDenoise → tbb, ispc
```

### Pre-compiled Libraries

**Location:** `lib/`

Platform-specific directories:
- `linux_x64/` - Linux x86_64
- `macos_arm64/` - macOS ARM64 (Apple Silicon)
- `windows_x64/` - Windows x86_64
- `windows_arm64/` - Windows ARM64

---

## 7. Python Integration

### Scripts Directory Structure

```
scripts/
├── addons_core/     # Built-in addons
├── freestyle/       # Freestyle Python
├── modules/         # Python modules
├── presets/         # Presets
├── site/            # Python site-packages
├── startup/         # Startup scripts
├── templates_osl/   # OSL templates
├── templates_py/    # Python templates
└── templates_toml/  # TOML templates
```

### Core Python Modules

| Module | Purpose |
|--------|---------|
| **bpy/** | Main Blender Python API |
| **bpy_extras/** | Additional utilities |
| **gpu_extras/** | GPU module extras |
| **bl_keymap_utils/** | Keymap utilities |
| **nodeitems_utils/** | Node menu utilities |
| **addon_utils.py** | Addon management |

### Built-in Addons

| Addon | Purpose |
|-------|---------|
| **io_scene_gltf2/** | glTF import/export |
| **io_scene_fbx/** | FBX import/export |
| **rigify/** | Rig generation |
| **node_wrangler/** | Node utilities |
| **io_anim_bvh/** | BVH motion capture |
| **io_curve_svg/** | SVG import |
| **hydra_storm/** | Hydra Storm engine |

---

## 8. Architectural Patterns

### 8.1 DNA/RNA System

**DNA (Data DNA):**
- Compile-time type definitions
- Binary serialization format
- Version-compatible file format
- Located in `makesdna/DNA_*_types.h`

**RNA (Runtime DNA):**
- Runtime type information
- Property reflection system
- Python API foundation
- UI automatic generation
- Located in `makesrna/`

### 8.2 Main Database Structure

**Main Struct (`BKE_main.hh`):**
- Root of all Blender data
- Contains lists of all ID data-blocks
- Not serialized directly (dumped as binary)
- Thread-safe access via locking

### 8.3 ID Data-block System

All major data types are ID blocks:
- Objects, Meshes, Curves
- Materials, Textures, Images
- Actions, Armatures
- Scenes, Collections
- Node trees, Worlds

**Features:**
- Reference counting
- Library linking
- Override system
- Unique naming

### 8.4 ListBase Linked Lists

**Foundation:** `DNA_listBase.h`

```c
struct ListBase {
  void *first, *last;
};

struct Link {
  struct Link *next, *prev;
};
```

All Blender lists use this foundation with C++ wrappers for type safety.

### 8.5 Span/Vector Pattern

Modern C++ patterns used throughout:
- `Span<T>` - Non-owning view (like `std::span`)
- `Vector<T>` - Owning dynamic array
- `Array<T>` - Fixed-size array
- `Set<T>`, `Map<K,V>` - Associative containers

### 8.6 Task System

**Parallel Evaluation:**
- `BLI_task.hh` - Task scheduler
- Work stealing
- Thread pool
- Used for: dependency graph evaluation, viewport drawing, rendering, simulation

### 8.7 Modifier System

**Stack-based Processing:**
- Modifiers applied in order
- Non-destructive workflow
- Evaluated on demand
- Types: Mesh, Curve, Grease Pencil

### 8.8 Node System Architecture

**Node Types:**
- Shader nodes
- Compositor nodes
- Geometry nodes
- Texture nodes

**Execution:**
- Lazy function system (Geometry Nodes)
- Multi-function procedures
- GPU acceleration

### 8.9 GHOST Event System

**Event Flow:**
1. Platform event (GHOST)
2. Event queue (WM)
3. Event handling (editors/operators)

**Event Types:**
- Keyboard, Mouse, Window
- Timer, NDOF (3D mouse), XR

---

## 9. Programming Languages

### Primary Languages

| Language | Usage | Percentage (approx.) |
|----------|-------|---------------------|
| **C++** | Core application, modern modules | ~60% |
| **C** | Legacy code, DNA, blenlib | ~25% |
| **Python** | Scripting, addons, tools | ~10% |
| **CMake** | Build system | ~3% |
| **Other** | Shaders (GLSL, OSL, Metal) | ~2% |

### C++ Standards

- **Minimum:** C++17
- **Preferred:** C++20 features where available
- Modern C++ patterns: smart pointers, templates, lambdas, range-based for loops

### Code Style

- **C++:** Google style with Blender modifications
- **Python:** PEP 8 with line length 120
- **Formatting:** clang-format, autopep8

---

## 10. Key Design Decisions

### 10.1 In-source DNA, Out-of-source RNA

- DNA structs defined in headers for serialization
- RNA definitions generated at runtime
- Separation allows independent evolution

### 10.2 Single Main Database

- All data in one `Main` struct
- Simplifies file I/O (binary dump)
- Enables undo/redo system
- Requires careful memory management

### 10.3 GHOST Abstraction

- Complete windowing abstraction
- Enables multi-platform support
- Consistent event handling
- XR integration point

### 10.4 GPU Abstraction Layer

- Unified API for OpenGL/Vulkan/Metal
- Shader cross-compilation
- Backend-agnostic rendering
- Enables EEVEE next-gen

### 10.5 Cycles Integration

- Separate codebase (`intern/cycles/`)
- Can build standalone
- Multiple device backends
- Kernel shared across devices

### 10.6 Python Integration

- Embedded interpreter
- Full API exposure via RNA
- Addon system
- Scripting for all subsystems

### 10.7 Dependency Graph

- Automatic dependency tracking
- Parallel evaluation
- Lazy evaluation where possible
- Supports complex rigging

### 10.8 Geometry Nodes

- Lazy function system
- Multi-threaded execution
- Field-based evaluation
- Non-destructive workflow

### 10.9 Asset System

- Catalog-based organization
- Library linking
- Remote libraries
- Essential library bundling

---

## 11. Testing Infrastructure

### Test Types

**Location:** `tests/`

| Test Type | Location | Purpose |
|-----------|----------|---------|
| **Python Tests** | `tests/python/` | API testing |
| **GTests** | `tests/gtests/` | C++ unit tests |
| **Performance** | `tests/performance/` | Benchmark tests |
| **Coverage** | `tests/coverage/` | Code coverage |
| **Files** | `tests/files/` | Test data |

### Build Testing

```bash
make test            # Run ctest
make check_pep8      # Python style
make check_mypy      # Python type checking
make check_cppcheck  # C++ static analysis
make check_clang_array  # Array bounds checking
```

---

## 12. Documentation

### Documentation Types

**Location:** `doc/`

| Type | Location | Generator |
|------|----------|-----------|
| **Python API** | `doc/python_api/` | Sphinx |
| **C/C++ API** | `doc/doxygen/` | Doxygen |
| **File Format** | `doc/blender_file_format/` | Custom |
| **Man Page** | `doc/manpage/` | Custom |
| **Guides** | `doc/guides/` | Manual |

### Build Documentation

```bash
make doc_py      # Python API docs
make doc_doxy    # C/C++ docs
make doc_dna     # DNA reference
make doc_man     # Man page
```

---

## Appendix A: Release Structure

**Location:** `release/`

```
release/
├── bin/              # Platform binaries
├── datafiles/        # Default data (startup.blend, icons, fonts)
├── extensions/       # Extensions
├── freedesktop/      # Linux desktop files
├── license/          # License files
├── lts/              # LTS information
├── pypi/             # Python packages
├── release_notes/    # Release notes
├── text/             # Text files
└── windows/          # Windows-specific
```

---

## Appendix B: Tools Directory

**Location:** `tools/`

| Tool Category | Purpose |
|--------------|---------|
| **check_source/** | Source code checking |
| **check_docs/** | Documentation checking |
| **utils/** | General utilities |
| **utils_build/** | Build utilities |
| **utils_doc/** | Documentation tools |
| **utils_ide/** | IDE integration |
| **utils_maintenance/** | Maintenance tools |
| **config/** | Configuration |
| **debug/** | Debugging tools |
| **git/** | Git utilities |

---

## Summary

Blender is a massive, modular 3D creation suite with sophisticated architecture emphasizing:

- **Modularity** - Clear separation of concerns across 100+ modules
- **Portability** - Platform abstraction via GHOST and GPU layers
- **Performance** - Parallel evaluation via dependency graph and task system
- **Extensibility** - Full Python API exposure via RNA system
- **Compatibility** - DNA/RNA versioning for file format stability
- **Maintainability** - Comprehensive testing, documentation, and code checking
