#!/usr/bin/env python3
"""
Prompt Templates Library for Blender MCP.

Pre-built prompt templates for common Blender automation tasks.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """A prompt template."""
    name: str
    description: str
    category: str
    template: str
    variables: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class PromptLibrary:
    """Library of prompt templates for Blender automation."""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all prompt templates."""
        
        # =====================================================================
        # Scene Creation Templates
        # =====================================================================
        
        self.templates["simple_scene"] = PromptTemplate(
            name="Simple Scene Creation",
            description="Create a basic scene with objects",
            category="scene_creation",
            template="""Create a Blender scene with the following:
- A ground plane at origin with {ground_material} material
- {object_count} {object_type} objects arranged in a {arrangement}
- A sun light for illumination
- A camera positioned to view the scene

Ground material color: {ground_color}
Object material color: {object_color}
""",
            variables=[
                "ground_material", "object_count", "object_type", 
                "arrangement", "ground_color", "object_color"
            ],
            examples=[
                "Create a scene with a gray ground plane, 5 red cubes in a circle, sun light, and camera",
                "Set up a scene with green grass ground, 10 blue spheres scattered randomly, and lighting"
            ]
        )

        self.templates["product_showcase"] = PromptTemplate(
            name="Product Showcase Scene",
            description="Create a professional product visualization scene",
            category="scene_creation",
            template="""Create a professional product showcase scene:

1. Create a studio environment:
   - Curved backdrop (cyclorama) with {backdrop_color} color
   - Floor with reflective {floor_material} material

2. Lighting setup (three-point lighting):
   - Key light: {key_light_intensity}W, positioned at {key_light_position}
   - Fill light: {fill_light_intensity}W, positioned at {fill_light_position}
   - Rim light: {rim_light_intensity}W, positioned at {rim_light_position}

3. Camera:
   - Position: {camera_position}
   - Focal length: {focal_length}mm
   - Pointing at origin

4. Product placeholder:
   - Create a {product_shape} at origin to represent the product
""",
            variables=[
                "backdrop_color", "floor_material",
                "key_light_intensity", "key_light_position",
                "fill_light_intensity", "fill_light_position",
                "rim_light_intensity", "rim_light_position",
                "camera_position", "focal_length", "product_shape"
            ],
            examples=[
                "Create a product showcase with white backdrop, marble floor, professional three-point lighting, and a box as product placeholder",
                "Set up a jewelry showcase with black backdrop, gold floor, and soft lighting"
            ]
        )

        self.templates["architectural_interior"] = PromptTemplate(
            name="Architectural Interior",
            description="Create a basic room interior",
            category="scene_creation",
            template="""Create a simple room interior:

1. Room structure:
   - Floor: {floor_size} meters, {floor_material} material
   - Walls: {wall_height} meters high, {wall_color} color
   - Ceiling: same as floor size

2. Windows:
   - {window_count} window(s) on {window_wall} wall
   - Window size: {window_size}

3. Furniture:
   - {furniture_list}

4. Lighting:
   - Natural light from windows
   - {ceiling_light_count} ceiling light(s)

5. Camera at human eye height ({camera_height}m) positioned at {camera_position}
""",
            variables=[
                "floor_size", "floor_material", "wall_height", "wall_color",
                "window_count", "window_wall", "window_size",
                "furniture_list", "ceiling_light_count", "camera_height", "camera_position"
            ],
            examples=[
                "Create a 5x4 meter room with 3m walls, white color, 2 windows on the front wall, a table and chair, and one ceiling light",
                "Create a modern living room with wooden floor, gray walls, large windows, sofa, coffee table, and floor lamp"
            ]
        )

        # =====================================================================
        # Animation Templates
        # =====================================================================

        self.templates["bouncing_ball"] = PromptTemplate(
            name="Bouncing Ball Animation",
            description="Create a bouncing ball animation",
            category="animation",
            template="""Create a bouncing ball animation:

1. Create a sphere with radius {radius} at position {start_position}
2. Apply {material_color} material
3. Animate from frame {start_frame} to {end_frame}:
   - Ball bounces {bounce_count} times
   - Maximum height: {max_height} meters
   - Each bounce is {decay_factor}% of previous height
4. Add squash and stretch:
   - Scale Z to {squash_factor} on impact
   - Scale X/Z to {stretch_factor} during fall
5. Set frame rate to {fps} fps
""",
            variables=[
                "radius", "start_position", "material_color",
                "start_frame", "end_frame", "bounce_count",
                "max_height", "decay_factor", "squash_factor", 
                "stretch_factor", "fps"
            ],
            examples=[
                "Create a bouncing ball animation, red ball, 5 bounces over 60 frames, max height 5 meters",
                "Animate a basketball bouncing with realistic squash and stretch, 3 bounces"
            ]
        )

        self.templates["camera_flythrough"] = PromptTemplate(
            name="Camera Fly-through Animation",
            description="Create a camera fly-through animation",
            category="animation",
            template="""Create a camera fly-through animation:

1. Create camera at {start_position}
2. Animate camera along path:
   - Waypoints: {waypoints}
   - Duration: {duration} frames
   - Easing: {easing_type}

3. Camera settings:
   - Focal length: {focal_length}mm
   - Point camera at: {look_at_position}

4. Output settings:
   - Resolution: {resolution}
   - Frame rate: {fps} fps
""",
            variables=[
                "start_position", "waypoints", "duration", "easing_type",
                "look_at_position", "focal_length", "resolution", "fps"
            ],
            examples=[
                "Create a camera fly-through starting at (10, 0, 5), passing through (0, 10, 5) and (-10, 0, 5), over 120 frames",
                "Animate a camera orbit around the origin, radius 15 meters, one full revolution in 90 frames"
            ]
        )

        self.templates["object_transformation"] = PromptTemplate(
            name="Object Transformation Animation",
            description="Animate object transformation",
            category="animation",
            template="""Animate object transformation:

1. Target object: {object_name}
2. Animation duration: {start_frame} to {end_frame}

3. Transform keyframes:
   - Start location: {start_location}
   - End location: {end_location}
   - Start rotation: {start_rotation}
   - End rotation: {end_rotation}
   - Start scale: {start_scale}
   - End scale: {end_scale}

4. Interpolation: {interpolation}
5. Add ease in/out: {ease_enabled}
""",
            variables=[
                "object_name", "start_frame", "end_frame",
                "start_location", "end_location",
                "start_rotation", "end_rotation",
                "start_scale", "end_scale",
                "interpolation", "ease_enabled"
            ],
            examples=[
                "Animate Cube moving from (0,0,0) to (10,10,10) over 60 frames with smooth interpolation",
                "Animate a sphere rotating 360 degrees on Y axis while scaling from 1 to 2"
            ]
        )

        # =====================================================================
        # Rigging Templates
        # =====================================================================

        self.templates["character_rig"] = PromptTemplate(
            name="Character Rig",
            description="Create a character rig",
            category="rigging",
            template="""Create a character rig:

1. Rig type: {rig_type}
2. Rig name: {rig_name}
3. Character height: {height} meters
4. Position: {location}

5. Additional features:
   - Finger controls: {finger_controls}
   - Face controls: {face_controls}
   - IK/FK switch: {ik_fk_switch}
   - Custom shapes: {custom_shapes}

6. After rigging, parent {mesh_name} to the rig with automatic weights
""",
            variables=[
                "rig_type", "rig_name", "height", "location",
                "finger_controls", "face_controls", "ik_fk_switch",
                "custom_shapes", "mesh_name"
            ],
            examples=[
                "Create a humanoid rig named 'HeroRig', 1.8 meters tall, with finger controls and IK/FK switch",
                "Create a simple biped rig for the character mesh, with automatic weight painting"
            ]
        )

        self.templates["mechanical_rig"] = PromptTemplate(
            name="Mechanical Rig",
            description="Create a mechanical/robotic rig",
            category="rigging",
            template="""Create a mechanical rig:

1. Object to rig: {object_name}
2. Rig type: {mech_type} (robotic arm, vehicle, etc.)

3. Joint chain:
   - Base joint at {base_position}
   - Joint count: {joint_count}
   - Joint length: {joint_length}
   - Rotation limits: {rotation_limits}

4. Controls:
   - IK target at end effector
   - Individual joint rotation controls
   - Master control at base
""",
            variables=[
                "object_name", "mech_type", "base_position",
                "joint_count", "joint_length", "rotation_limits"
            ],
            examples=[
                "Create a robotic arm rig with 4 joints, each 1 meter long, with 180 degree rotation limits",
                "Create a simple vehicle rig with wheel controls for the car object"
            ]
        )

        # =====================================================================
        # Material Templates
        # =====================================================================

        self.templates["pbr_material"] = PromptTemplate(
            name="PBR Material Creation",
            description="Create a PBR material",
            category="materials",
            template="""Create a PBR material:

1. Material name: {material_name}
2. Base color: {base_color}
3. Metallic: {metallic} (0-1)
4. Roughness: {roughness} (0-1)
5. Normal strength: {normal_strength}
6. Apply to object: {object_name}

Additional PBR maps (if available):
- Albedo texture: {albedo_texture}
- Roughness texture: {roughness_texture}
- Metallic texture: {metallic_texture}
- Normal map: {normal_map}
""",
            variables=[
                "material_name", "base_color", "metallic", "roughness",
                "normal_strength", "object_name",
                "albedo_texture", "roughness_texture", "metallic_texture", "normal_map"
            ],
            examples=[
                "Create a gold material with metallic 1.0, roughness 0.3, apply to ring object",
                "Create a concrete material with gray base color, roughness 0.9, metallic 0"
            ]
        )

        self.templates["glass_material"] = PromptTemplate(
            name="Glass Material",
            description="Create a realistic glass material",
            category="materials",
            template="""Create a glass material:

1. Material name: {material_name}
2. Glass type: {glass_type} (clear, frosted, colored, mirror)
3. Base color: {base_color}
4. Transmission: {transmission} (0-1)
5. Roughness: {roughness} (0-1)
6. IOR: {ior} (typically 1.45-1.55 for glass)
7. Thickness: {thickness} for volume absorption

Apply to: {object_name}
""",
            variables=[
                "material_name", "glass_type", "base_color",
                "transmission", "roughness", "ior", "thickness", "object_name"
            ],
            examples=[
                "Create a clear glass material with IOR 1.5, transmission 1.0, apply to wine_glass object",
                "Create a frosted glass material with roughness 0.5, light blue tint"
            ]
        )

        # =====================================================================
        # Batch Processing Templates
        # =====================================================================

        self.templates["batch_export"] = PromptTemplate(
            name="Batch Export",
            description="Export multiple objects",
            category="batch",
            template="""Batch export objects:

1. Export format: {format}
2. Output directory: {directory}
3. Objects to export:
   - Filter by type: {object_type}
   - Filter by name pattern: {name_pattern}
   - Or specific objects: {object_list}

4. Export settings:
   - Individual files: {individual_files}
   - Include materials: {include_materials}
   - Include animations: {include_animations}
   - Apply modifiers: {apply_modifiers}
""",
            variables=[
                "format", "directory", "object_type", "name_pattern",
                "object_list", "individual_files", "include_materials",
                "include_animations", "apply_modifiers"
            ],
            examples=[
                "Export all mesh objects as individual FBX files to /exports folder, include materials",
                "Export all objects with 'Prop_' prefix as OBJ files"
            ]
        )

        self.templates["scene_cleanup"] = PromptTemplate(
            name="Scene Cleanup",
            description="Clean up unused data",
            category="batch",
            template="""Clean up the scene:

1. Remove unused data blocks:
   - Materials: {remove_materials}
   - Meshes: {remove_meshes}
   - Textures: {remove_textures}
   - Images: {remove_images}
   - Armatures: {remove_armatures}
   - Actions: {remove_actions}

2. Recalculate:
   - Normals: {recalc_normals}
   - UVs: {recalc_uvs}

3. Apply modifiers: {apply_modifiers}
4. Remove doubles: {remove_doubles}
""",
            variables=[
                "remove_materials", "remove_meshes", "remove_textures",
                "remove_images", "remove_armatures", "remove_actions",
                "recalc_normals", "recalc_uvs", "apply_modifiers", "remove_doubles"
            ],
            examples=[
                "Clean up the scene by removing all unused materials, meshes, and textures, recalculate normals",
                "Full cleanup: remove all unused data, apply all modifiers, remove doubles"
            ]
        )

        # =====================================================================
        # Geometry Nodes Templates
        # =====================================================================

        self.templates["geo_nodes_scatter"] = PromptTemplate(
            name="Geometry Nodes Scatter",
            description="Scatter objects using Geometry Nodes",
            category="geometry_nodes",
            template="""Create Geometry Nodes scatter system:

1. Base object (surface): {base_object}
2. Instance object (to scatter): {instance_object}
3. Distribution:
   - Method: {distribution_method} (random, grid, poisson)
   - Count: {count}
   - Density: {density}

4. Randomization:
   - Scale random: {scale_random}
   - Rotation random: {rotation_random}
   - Align to normal: {align_normal}

5. Add Geometry Nodes modifier to {base_object}
""",
            variables=[
                "base_object", "instance_object", "distribution_method",
                "count", "density", "scale_random", "rotation_random",
                "align_normal"
            ],
            examples=[
                "Scatter 100 trees on the terrain mesh with random scale and rotation",
                "Create grass instances on ground using Geometry Nodes, density 50 per square meter"
            ]
        )

        self.templates["geo_nodes_modeling"] = PromptTemplate(
            name="Geometry Nodes Procedural Modeling",
            description="Create procedural model with Geometry Nodes",
            category="geometry_nodes",
            template="""Create procedural model with Geometry Nodes:

1. Target object: {object_name}
2. Modeling operation: {operation}

3. Parameters:
   {parameters}

4. Add Geometry Nodes modifier and setup node tree
""",
            variables=[
                "object_name", "operation", "parameters"
            ],
            examples=[
                "Create a procedural building generator with adjustable floors, width, and window count",
                "Create a procedural rope/chain generator with adjustable link size and count"
            ]
        )

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get all templates in a category."""
        return [
            t for t in self.templates.values() 
            if t.category == category
        ]

    def render_template(self, name: str, **kwargs) -> str:
        """Render a template with provided variables."""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        result = template.template
        for var in template.variables:
            placeholder = "{" + var + "}"
            value = kwargs.get(var, f"[{var}]")
            result = result.replace(placeholder, str(value))

        return result

    def list_templates(self) -> List[Dict]:
        """List all available templates."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "variables": t.variables,
                "examples": t.examples
            }
            for t in self.templates.values()
        ]


# Global library instance
_library: Optional[PromptLibrary] = None


def get_prompt_library() -> PromptLibrary:
    """Get the global prompt library instance."""
    global _library
    if _library is None:
        _library = PromptLibrary()
    return _library


def render_prompt(name: str, **kwargs) -> str:
    """Render a prompt template."""
    return get_prompt_library().render_template(name, **kwargs)


def list_prompts() -> List[Dict]:
    """List all available prompts."""
    return get_prompt_library().list_templates()
