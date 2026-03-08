#!/usr/bin/env python3
"""
Blender Tools - Core tool implementations for MCP server.

This module provides the actual Blender API implementations
for all MCP tools.
"""

import bpy
import math
from typing import Optional


class BlenderTools:
    """Collection of Blender operations for MCP server."""

    # Object type mapping for creation
    OBJECT_CREATORS = {
        "cube": lambda: bpy.ops.mesh.primitive_cube_add(),
        "sphere": lambda: bpy.ops.mesh.primitive_uv_sphere_add(),
        "cylinder": lambda: bpy.ops.mesh.primitive_cylinder_add(),
        "cone": lambda: bpy.ops.mesh.primitive_cone_add(),
        "torus": lambda: bpy.ops.mesh.primitive_torus_add(),
        "plane": lambda: bpy.ops.mesh.primitive_plane_add(),
    }

    def create_object(
        self,
        type: str,
        location: Optional[list[float]] = None,
        rotation: Optional[list[float]] = None,
        scale: Optional[list[float]] = None,
        name: Optional[str] = None,
        radius: Optional[float] = None,
        depth: Optional[float] = None,
        energy: Optional[float] = None,
        color: Optional[list[float]] = None,
    ) -> dict:
        """Create a 3D primitive object."""
        
        # Handle special types (light, camera)
        if type == "light":
            return self._create_light_internal(
                light_type="POINT",
                location=location,
                energy=energy,
                color=color,
                name=name
            )
        elif type == "camera":
            return self._create_camera_internal(
                location=location,
                rotation=rotation,
                name=name
            )

        # Check if type is supported
        if type not in self.OBJECT_CREATORS:
            raise ValueError(f"Unknown object type: {type}. Supported: {list(self.OBJECT_CREATORS.keys())}")

        # Store current selection
        prev_active = bpy.context.view_layer.objects.active
        prev_selected = [obj for obj in bpy.context.selected_objects]

        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # Create the object with parameters
        kwargs = {}
        if location:
            kwargs['location'] = tuple(location)
        if rotation:
            kwargs['rotation_euler'] = tuple(math.radians(r) for r in rotation)
        if radius and type in ["sphere", "cylinder", "cone", "torus"]:
            kwargs['radius'] = radius
        if depth and type in ["cylinder", "cone"]:
            kwargs['depth'] = depth

        # Create the object
        self.OBJECT_CREATORS[type]()

        # Get the newly created object
        new_obj = bpy.context.active_object

        # Apply scale if provided
        if scale:
            new_obj.scale = tuple(scale)

        # Rename if provided
        if name:
            new_obj.name = name

        # Restore previous selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in prev_selected:
            obj.select_set(True)
        if prev_active:
            bpy.context.view_layer.objects.active = prev_active

        return {
            "success": True,
            "object_name": new_obj.name,
            "object_type": new_obj.type,
            "location": list(new_obj.location),
            "rotation": [math.degrees(a) for a in new_obj.rotation_euler],
            "scale": list(new_obj.scale)
        }

    def delete_object(self, name: str) -> dict:
        """Delete an object from the scene."""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        # Store name for response
        obj_name = obj.name
        obj_type = obj.type

        # Delete the object
        bpy.data.objects.remove(obj, do_unlink=True)

        return {
            "success": True,
            "deleted_object": obj_name,
            "object_type": obj_type
        }

    def get_scene_info(self) -> dict:
        """Get information about the current scene."""
        scene = bpy.context.scene
        objects = []

        for obj in scene.objects:
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": [math.degrees(a) for a in obj.rotation_euler],
                "scale": list(obj.scale),
                "selected": obj.select_get(),
                "hidden": obj.hide_get(),
                "visible_camera": obj.visible_camera_get(),
            })

        # Get render settings
        render = scene.render
        return {
            "scene_name": scene.name,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "fps": scene.render.fps,
            "resolution": {
                "x": render.resolution_x,
                "y": render.resolution_y,
                "percentage": render.resolution_percentage
            },
            "render_engine": scene.render.engine,
            "objects": objects,
            "object_count": len(objects),
            "camera": scene.camera.name if scene.camera else None,
        }

    def get_object_info(self, name: str) -> dict:
        """Get detailed information about a specific object."""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        info = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": [math.degrees(a) for a in obj.rotation_euler],
            "scale": list(obj.scale),
            "dimensions": list(obj.dimensions),
            "selected": obj.select_get(),
            "hidden": obj.hide_get(),
        }

        # Add type-specific info
        if obj.type == 'MESH':
            mesh = obj.data
            info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons)
            }
        elif obj.type == 'CAMERA':
            cam = obj.data
            info["camera"] = {
                "type": cam.type,
                "focal_length": cam.lens,
                "sensor_width": cam.sensor_width,
                "clip_start": cam.clip_start,
                "clip_end": cam.clip_end
            }
        elif obj.type == 'LIGHT':
            light = obj.data
            info["light"] = {
                "type": light.type,
                "energy": light.energy,
                "color": list(light.color),
                "shadow_soft_size": light.shadow_soft_size
            }
        elif obj.type == 'MATERIAL':
            info["materials"] = [mat.name for mat in obj.data.materials if mat]

        return info

    def modify_object(
        self,
        name: str,
        location: Optional[list[float]] = None,
        rotation: Optional[list[float]] = None,
        scale: Optional[list[float]] = None,
    ) -> dict:
        """Modify an object's transform."""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        if location:
            obj.location = tuple(location)
        if rotation:
            obj.rotation_euler = tuple(math.radians(r) for r in rotation)
        if scale:
            obj.scale = tuple(scale)

        return {
            "success": True,
            "object_name": obj.name,
            "location": list(obj.location),
            "rotation": [math.degrees(a) for a in obj.rotation_euler],
            "scale": list(obj.scale)
        }

    def set_material(
        self,
        object_name: str,
        material_name: str,
        color: Optional[list[float]] = None,
        metallic: Optional[float] = None,
        roughness: Optional[float] = None,
    ) -> dict:
        """Create or apply a material to an object."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        # Get or create material
        mat = bpy.data.materials.get(material_name)
        if not mat:
            mat = bpy.data.materials.new(name=material_name)
            mat.use_nodes = True

        # Configure material
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                if color:
                    alpha = color[3] if len(color) > 3 else 1.0
                    bsdf.inputs["Base Color"].default_value = (*color[:3], alpha)
                if metallic is not None:
                    bsdf.inputs["Metallic"].default_value = metallic
                if roughness is not None:
                    bsdf.inputs["Roughness"].default_value = roughness

        # Apply material to object
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat

        return {
            "success": True,
            "material_name": mat.name,
            "object_name": object_name,
            "color": color,
            "metallic": metallic,
            "roughness": roughness
        }

    def _create_camera_internal(
        self,
        location: Optional[list[float]] = None,
        rotation: Optional[list[float]] = None,
        name: Optional[str] = None,
        focal_length: Optional[float] = None,
    ) -> dict:
        """Internal method to create a camera."""
        bpy.ops.object.camera_add()
        cam = bpy.context.active_object

        if location:
            cam.location = tuple(location)
        if rotation:
            cam.rotation_euler = tuple(math.radians(r) for r in rotation)
        if name:
            cam.name = name
        if focal_length:
            cam.data.lens = focal_length

        # Set as active camera
        bpy.context.scene.camera = cam

        return {
            "success": True,
            "object_name": cam.name,
            "focal_length": cam.data.lens,
            "location": list(cam.location),
            "is_active_camera": True
        }

    def create_camera(
        self,
        location: Optional[list[float]] = None,
        rotation: Optional[list[float]] = None,
        name: Optional[str] = None,
        focal_length: Optional[float] = None,
    ) -> dict:
        """Add a camera to the scene."""
        return self._create_camera_internal(
            location=location,
            rotation=rotation,
            name=name,
            focal_length=focal_length
        )

    def _create_light_internal(
        self,
        light_type: str = "POINT",
        location: Optional[list[float]] = None,
        energy: Optional[float] = None,
        color: Optional[list[float]] = None,
        name: Optional[str] = None,
    ) -> dict:
        """Internal method to create a light."""
        bpy.ops.object.light_add(type=light_type)
        light = bpy.context.active_object

        if location:
            light.location = tuple(location)
        if name:
            light.name = name
        if energy:
            light.data.energy = energy
        if color:
            light.data.color = tuple(color[:3])

        return {
            "success": True,
            "object_name": light.name,
            "light_type": light.data.type,
            "energy": light.data.energy,
            "color": list(light.data.color),
            "location": list(light.location)
        }

    def create_light(
        self,
        type: str,
        location: Optional[list[float]] = None,
        energy: Optional[float] = None,
        color: Optional[list[float]] = None,
        name: Optional[str] = None,
    ) -> dict:
        """Add a light source to the scene."""
        return self._create_light_internal(
            light_type=type,
            location=location,
            energy=energy,
            color=color,
            name=name
        )

    def render_scene(
        self,
        filepath: Optional[str] = None,
        resolution_x: Optional[int] = None,
        resolution_y: Optional[int] = None,
        samples: Optional[int] = None,
    ) -> dict:
        """Render the current scene to an image file."""
        scene = bpy.context.scene
        render = scene.render

        # Store original settings
        orig_filepath = render.filepath
        orig_res_x = render.resolution_x
        orig_res_y = render.resolution_y

        # Apply new settings
        if filepath:
            render.filepath = filepath
        if resolution_x:
            render.resolution_x = resolution_x
        if resolution_y:
            render.resolution_y = resolution_y
        if samples:
            scene.cycles.samples = samples

        # Render
        bpy.ops.render.render(write_still=True)

        # Restore original settings
        render.filepath = orig_filepath
        render.resolution_x = orig_res_x
        render.resolution_y = orig_res_y

        return {
            "success": True,
            "filepath": filepath or render.filepath,
            "resolution": {
                "x": render.resolution_x,
                "y": render.resolution_y
            }
        }

    def export_file(
        self,
        filepath: str,
        format: str,
        use_selection: bool = False,
    ) -> dict:
        """Export the scene or selected objects to a file."""
        format = format.upper()

        exporters = {
            "FBX": lambda: bpy.ops.export_scene.fbx(filepath=filepath, use_selection=use_selection),
            "OBJ": lambda: bpy.ops.export_scene.obj(filepath=filepath, use_selection=use_selection),
            "GLTF": lambda: bpy.ops.export_scene.gltf(filepath=filepath, use_selection=use_selection),
            "STL": lambda: bpy.ops.export_mesh.stl(filepath=filepath, use_selection=use_selection),
            "PLY": lambda: bpy.ops.export_mesh.ply(filepath=filepath, use_selection=use_selection),
        }

        if format not in exporters:
            raise ValueError(f"Unsupported format: {format}. Supported: {list(exporters.keys())}")

        exporters[format]()

        return {
            "success": True,
            "filepath": filepath,
            "format": format,
            "selection_only": use_selection
        }

    def clear_scene(self, confirm: bool) -> dict:
        """Remove all objects from the scene."""
        if not confirm:
            raise ValueError("Must provide confirm=true to clear scene")

        # Store count
        count = len(bpy.context.scene.objects)

        # Delete all objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        return {
            "success": True,
            "deleted_count": count
        }
