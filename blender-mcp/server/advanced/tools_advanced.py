#!/usr/bin/env python3
"""
Advanced Blender Tools - Rigging, Animation, Batch Processing, Geometry Nodes.

This module extends the basic tools with advanced functionality for:
- Character rigging
- Animation keyframing
- Batch operations
- Geometry Nodes manipulation
"""

import bpy
import math
import random
from typing import Optional, List, Dict, Any
from mathutils import Vector, Euler, Quaternion


class AdvancedBlenderTools:
    """Advanced Blender operations for MCP server."""

    # =========================================================================
    # Rigging Tools
    # =========================================================================

    def create_armature(
        self,
        name: str = "Armature",
        location: Optional[List[float]] = None,
        bone_names: Optional[List[str]] = None,
    ) -> dict:
        """Create an armature object for rigging."""
        # Create armature data
        armature_data = bpy.data.armatures.new(name=name)
        armature_obj = bpy.data.objects.new(name, armature_data)

        # Set location
        if location:
            armature_obj.location = tuple(location)

        # Link to scene
        bpy.context.collection.objects.link(armature_obj)

        # Set as active
        bpy.context.view_layer.objects.active = armature_obj
        armature_obj.select_set(True)

        # Enter edit mode to add bones
        bpy.ops.object.mode_set(mode='EDIT')

        # Create bones if names provided
        if bone_names:
            self._create_bone_chain(armature_data, bone_names)

        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        return {
            "success": True,
            "armature_name": armature_obj.name,
            "bone_count": len(armature_data.bones) if bone_names else 0,
            "location": list(armature_obj.location)
        }

    def _create_bone_chain(self, armature_data, bone_names: List[str], 
                          start_pos: Vector = Vector((0, 0, 0)),
                          direction: Vector = Vector((0, 0, 1)),
                          length: float = 1.0):
        """Create a chain of bones."""
        current_pos = start_pos.copy()

        for i, name in enumerate(bone_names):
            bone = armature_data.edit_bones.new(name)
            bone.head = current_pos
            bone.tail = current_pos + direction * length

            # Parent to previous bone
            if i > 0:
                bone.parent = armature_data.edit_bones[bone_names[i-1]]

            current_pos = bone.tail

    def create_humanoid_rig(
        self,
        name: str = "HumanoidRig",
        height: float = 2.0,
        location: Optional[List[float]] = None
    ) -> dict:
        """Create a basic humanoid rig with spine, arms, and legs."""
        # Create armature
        result = self.create_armature(name=name, location=location)
        armature_obj = bpy.data.objects.get(name)
        armature_data = armature_obj.data

        # Enter edit mode
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Calculate proportions
        spine_length = height * 0.35
        head_length = height * 0.15
        limb_length = height * 0.25

        # Create spine chain
        spine_bones = ["spine_01", "spine_02", "spine_03", "neck", "head"]
        self._create_bone_chain(
            armature_data, 
            spine_bones,
            start_pos=Vector((0, 0, 0)),
            direction=Vector((0, 0, 1)),
            length=spine_length
        )

        # Create legs
        for side in ["L", "R"]:
            x_offset = 0.15 if side == "R" else -0.15
            
            # Hip
            hip = armature_data.edit_bones.new(f"hip_{side}")
            hip.head = Vector((x_offset, 0, 0))
            hip.tail = Vector((x_offset, 0, -limb_length * 0.5))
            hip.parent = armature_data.edit_bones["spine_01"]

            # Upper leg
            upper_leg = armature_data.edit_bones.new(f"upper_leg_{side}")
            upper_leg.head = hip.tail
            upper_leg.tail = Vector((x_offset, 0, -limb_length * 1.5))
            upper_leg.parent = hip

            # Lower leg
            lower_leg = armature_data.edit_bones.new(f"lower_leg_{side}")
            lower_leg.head = upper_leg.tail
            lower_leg.tail = Vector((x_offset, limb_length * 0.3, -limb_length * 2.5))
            lower_leg.parent = upper_leg

            # Foot
            foot = armature_data.edit_bones.new(f"foot_{side}")
            foot.head = lower_leg.tail
            foot.tail = Vector((x_offset, limb_length * 0.8, -limb_length * 2.5))
            foot.parent = lower_leg

            # Arm
            shoulder_x = x_offset * 2
            shoulder = armature_data.edit_bones.new(f"shoulder_{side}")
            shoulder.head = Vector((shoulder_x, 0, spine_length * 0.9))
            shoulder.tail = Vector((shoulder_x * 1.5, 0, spine_length * 0.9))
            shoulder.parent = armature_data.edit_bones["spine_03"]

            upper_arm = armature_data.edit_bones.new(f"upper_arm_{side}")
            upper_arm.head = shoulder.tail
            upper_arm.tail = Vector((shoulder_x * 2, 0, spine_length * 0.9 - limb_length * 0.5))
            upper_arm.parent = shoulder

            lower_arm = armature_data.edit_bones.new(f"lower_arm_{side}")
            lower_arm.head = upper_arm.tail
            lower_arm.tail = Vector((shoulder_x * 2.5, 0, spine_length * 0.9 - limb_length))
            lower_arm.parent = upper_arm

            hand = armature_data.edit_bones.new(f"hand_{side}")
            hand.head = lower_arm.tail
            hand.tail = Vector((shoulder_x * 3, 0, spine_length * 0.9 - limb_length * 1.2))
            hand.parent = lower_arm

        bpy.ops.object.mode_set(mode='OBJECT')

        return {
            "success": True,
            "armature_name": name,
            "bone_count": len(armature_data.bones),
            "height": height,
            "rig_type": "humanoid"
        }

    def auto_weight_paint(
        self,
        mesh_object: str,
        armature_object: str
    ) -> dict:
        """Automatically assign vertex weights from armature."""
        mesh_obj = bpy.data.objects.get(mesh_object)
        armature_obj = bpy.data.objects.get(armature_object)

        if not mesh_obj:
            raise ValueError(f"Mesh object not found: {mesh_object}")
        if not armature_obj:
            raise ValueError(f"Armature object not found: {armature_object}")

        # Add armature modifier
        modifier = mesh_obj.modifiers.new(
            name="Armature",
            type='ARMATURE'
        )
        modifier.object = armature_obj

        # Parent mesh to armature with automatic weights
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        armature_obj.select_set(True)
        bpy.context.view_layer.objects.active = armature_obj

        bpy.ops.object.parent_set(type='ARMATURE_AUTO')

        return {
            "success": True,
            "mesh": mesh_object,
            "armature": armature_object,
            "modifier_added": True
        }

    def create_simple_rig(
        self,
        object_name: str,
        rig_type: str = "simple"
    ) -> dict:
        """Create a simple rig for an object."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        # Create armature at object location
        rig_name = f"{object_name}_Rig"
        armature_data = bpy.data.armatures.new(name=rig_name)
        rig_obj = bpy.data.objects.new(rig_name, armature_data)
        rig_obj.location = obj.location

        bpy.context.collection.objects.link(rig_obj)

        # Enter edit mode
        bpy.context.view_layer.objects.active = rig_obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Create control bone
        bone = armature_data.edit_bones.new("root")
        bone.head = Vector((0, 0, 0))
        bone.tail = Vector((0, 0, 1))

        bpy.ops.object.mode_set(mode='OBJECT')

        # Parent object to rig
        obj.select_set(True)
        rig_obj.select_set(True)
        bpy.context.view_layer.objects.active = rig_obj
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')

        return {
            "success": True,
            "rig_name": rig_name,
            "object": object_name
        }

    # =========================================================================
    # Animation Tools
    # =========================================================================

    def create_keyframe(
        self,
        object_name: str,
        frame: int,
        data_path: str = "location",
        value: Optional[List[float]] = None,
        index: Optional[int] = None
    ) -> dict:
        """Insert a keyframe for an object property."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        # Set the value if provided
        if value is not None:
            prop = getattr(obj, data_path)
            if index is not None:
                prop[index] = value[0] if isinstance(value, list) else value
            else:
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        prop[i] = v
                else:
                    setattr(obj, data_path, value)

        # Insert keyframe
        obj.keyframe_insert(data_path=data_path, index=index, frame=frame)

        return {
            "success": True,
            "object": object_name,
            "frame": frame,
            "data_path": data_path
        }

    def animate_location(
        self,
        object_name: str,
        keyframes: List[Dict[str, Any]],
        interpolation: str = "BEZIER"
    ) -> dict:
        """Animate object location with multiple keyframes.

        Args:
            object_name: Name of object to animate
            keyframes: List of {frame: int, location: [x, y, z]} dicts
            interpolation: Keyframe interpolation type
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        for kf in keyframes:
            frame = kf.get("frame", 1)
            location = kf.get("location", list(obj.location))

            obj.location = tuple(location)
            obj.keyframe_insert(data_path="location", frame=frame)

            # Set interpolation
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "location":
                    for keyframe_point in fcurve.keyframe_points:
                        if keyframe_point.co.x == frame:
                            keyframe_point.interpolation = interpolation

        return {
            "success": True,
            "object": object_name,
            "keyframe_count": len(keyframes)
        }

    def animate_rotation(
        self,
        object_name: str,
        keyframes: List[Dict[str, Any]]
    ) -> dict:
        """Animate object rotation with multiple keyframes."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        for kf in keyframes:
            frame = kf.get("frame", 1)
            rotation = kf.get("rotation", [0, 0, 0])

            # Convert degrees to radians
            obj.rotation_euler = Euler(
                (math.radians(r) for r in rotation),
                'XYZ'
            )
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "object": object_name,
            "keyframe_count": len(keyframes)
        }

    def animate_scale(
        self,
        object_name: str,
        keyframes: List[Dict[str, Any]]
    ) -> dict:
        """Animate object scale with multiple keyframes."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        for kf in keyframes:
            frame = kf.get("frame", 1)
            scale = kf.get("scale", [1, 1, 1])

            obj.scale = tuple(scale)
            obj.keyframe_insert(data_path="scale", frame=frame)

        return {
            "success": True,
            "object": object_name,
            "keyframe_count": len(keyframes)
        }

    def create_bouncing_ball_animation(
        self,
        object_name: str,
        start_frame: int = 1,
        end_frame: int = 60,
        bounce_height: float = 5.0,
        bounces: int = 3
    ) -> dict:
        """Create a bouncing ball animation."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        if obj.type != 'MESH':
            raise ValueError(f"Object must be a mesh, got: {obj.type}")

        frame_range = end_frame - start_frame
        bounce_interval = frame_range / bounces

        for bounce in range(bounces + 1):
            # Start of bounce (at ground)
            start_frame_num = start_frame + bounce * bounce_interval
            obj.location.z = 0
            obj.keyframe_insert(data_path="location", frame=int(start_frame_num))

            # Peak of bounce
            if bounce < bounces:
                peak_frame = start_frame_num + bounce_interval / 2
                peak_height = bounce_height * (0.7 ** bounce)  # Each bounce is lower
                obj.location.z = peak_height
                obj.keyframe_insert(data_path="location", frame=int(peak_frame))

                # End of bounce (back at ground)
                end_frame_num = start_frame_num + bounce_interval
                obj.location.z = 0
                obj.keyframe_insert(data_path="location", frame=int(end_frame_num))

        # Set final position
        obj.location.z = 0
        obj.keyframe_insert(data_path="location", frame=end_frame)

        return {
            "success": True,
            "object": object_name,
            "bounces": bounces,
            "max_height": bounce_height,
            "frame_range": [start_frame, end_frame]
        }

    def create_camera_animation(
        self,
        camera_name: str,
        animation_type: str,
        target_object: Optional[str] = None,
        frames: int = 100
    ) -> dict:
        """Create predefined camera animations."""
        camera = bpy.data.objects.get(camera_name)
        if not camera:
            raise ValueError(f"Camera not found: {camera_name}")

        if animation_type == "orbit":
            target = bpy.data.objects.get(target_object) if target_object else None
            target_pos = target.location if target else Vector((0, 0, 0))

            radius = 10
            for frame in range(frames):
                angle = (frame / frames) * 2 * math.pi
                camera.location.x = target_pos.x + math.cos(angle) * radius
                camera.location.y = target_pos.y + math.sin(angle) * radius
                camera.location.z = target_pos.z + 5
                camera.keyframe_insert(data_path="location", frame=frame)

                # Look at target
                direction = target_pos - camera.location
                rot_quat = direction.to_track_quat('Z', 'Y')
                camera.rotation_euler = rot_quat.to_euler()
                camera.keyframe_insert(data_path="rotation_euler", frame=frame)

        elif animation_type == "pan":
            start_pos = camera.location.copy()
            for frame in range(frames):
                t = frame / frames
                camera.location.x = start_pos.x + t * 20
                camera.keyframe_insert(data_path="location", frame=frame)

        elif animation_type == "zoom":
            for frame in range(frames):
                t = frame / frames
                camera.data.lens = 35 + t * 70  # 35mm to 105mm
                camera.keyframe_insert(data_path="data.lens", frame=frame)

        return {
            "success": True,
            "camera": camera_name,
            "animation_type": animation_type,
            "frames": frames
        }

    def set_animation_range(
        self,
        start_frame: int,
        end_frame: int,
        fps: int = 24
    ) -> dict:
        """Set the scene animation range."""
        scene = bpy.context.scene
        scene.frame_start = start_frame
        scene.frame_end = end_frame
        scene.render.fps = fps

        return {
            "success": True,
            "frame_start": start_frame,
            "frame_end": end_frame,
            "fps": fps,
            "duration_seconds": (end_frame - start_frame) / fps
        }

    # =========================================================================
    # Batch Processing Tools
    # =========================================================================

    def batch_export(
        self,
        directory: str,
        format: str = "FBX",
        individual_objects: bool = True,
        use_selection: bool = False
    ) -> dict:
        """Export multiple objects to individual files."""
        scene = bpy.context.scene
        exported = []

        if individual_objects:
            # Deselect all
            bpy.ops.object.select_all(action='DESELECT')

            for obj in scene.objects:
                if use_selection and not obj.select_get():
                    continue

                # Select only this object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                scene.objects.active = obj

                # Export
                filepath = f"{directory}/{obj.name}.{format.lower()}"
                try:
                    if format.upper() == "FBX":
                        bpy.ops.export_scene.fbx(
                            filepath=filepath,
                            use_selection=True,
                            use_active_collection=False
                        )
                    elif format.upper() == "OBJ":
                        bpy.ops.export_scene.obj(
                            filepath=filepath,
                            use_selection=True
                        )
                    elif format.upper() == "GLTF":
                        bpy.ops.export_scene.gltf(
                            filepath=filepath,
                            use_selection=True
                        )

                    exported.append(obj.name)
                except Exception as e:
                    print(f"Error exporting {obj.name}: {e}")
        else:
            # Export entire scene
            filepath = f"{directory}/scene.{format.lower()}"
            if format.upper() == "FBX":
                bpy.ops.export_scene.fbx(filepath=filepath)
            elif format.upper() == "OBJ":
                bpy.ops.export_scene.obj(filepath=filepath)
            elif format.upper() == "GLTF":
                bpy.ops.export_scene.gltf(filepath=filepath)
            exported.append("scene")

        return {
            "success": True,
            "format": format,
            "directory": directory,
            "exported_count": len(exported),
            "exported": exported
        }

    def batch_import(
        self,
        directory: str,
        format: str = "FBX"
    ) -> dict:
        """Import multiple files from a directory."""
        import os

        imported = []

        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        for filename in os.listdir(directory):
            if filename.lower().endswith(f".{format.lower()}"):
                filepath = os.path.join(directory, filename)
                try:
                    if format.upper() == "FBX":
                        bpy.ops.import_scene.fbx(filepath=filepath)
                    elif format.upper() == "OBJ":
                        bpy.ops.import_scene.obj(filepath=filepath)
                    elif format.upper() == "GLTF":
                        bpy.ops.import_scene.gltf(filepath=filepath)

                    imported.append(filename)
                except Exception as e:
                    print(f"Error importing {filename}: {e}")

        return {
            "success": True,
            "format": format,
            "directory": directory,
            "imported_count": len(imported),
            "imported": imported
        }

    def batch_rename(
        self,
        pattern: str,
        replacement: str,
        object_type: Optional[str] = None,
        use_regex: bool = False
    ) -> dict:
        """Batch rename objects based on pattern."""
        import re

        renamed = []

        for obj in bpy.context.scene.objects:
            if object_type and obj.type != object_type:
                continue

            try:
                if use_regex:
                    new_name = re.sub(pattern, replacement, obj.name)
                else:
                    new_name = obj.name.replace(pattern, replacement)

                if new_name != obj.name and new_name:
                    # Check if name is unique
                    if new_name not in bpy.data.objects:
                        obj.name = new_name
                        renamed.append((obj.name, new_name))
            except Exception as e:
                print(f"Error renaming {obj.name}: {e}")

        return {
            "success": True,
            "renamed_count": len(renamed),
            "renamed": renamed
        }

    def batch_apply_material(
        self,
        material_name: str,
        object_type: Optional[str] = None,
        objects: Optional[List[str]] = None
    ) -> dict:
        """Apply a material to multiple objects."""
        material = bpy.data.materials.get(material_name)
        if not material:
            raise ValueError(f"Material not found: {material_name}")

        applied = []

        if objects:
            target_objects = [bpy.data.objects.get(name) for name in objects]
            target_objects = [obj for obj in target_objects if obj]
        else:
            target_objects = bpy.context.scene.objects

        for obj in target_objects:
            if object_type and obj.type != object_type:
                continue

            if obj.type == 'MESH':
                if len(obj.material_slots) == 0:
                    obj.data.materials.append(material)
                else:
                    obj.material_slots[0].material = material
                applied.append(obj.name)

        return {
            "success": True,
            "material": material_name,
            "applied_count": len(applied),
            "applied": applied
        }

    def cleanup_unused_data(
        self,
        materials: bool = True,
        meshes: bool = True,
        textures: bool = True,
        images: bool = True
    ) -> dict:
        """Remove unused data blocks from the file."""
        removed = {
            "materials": 0,
            "meshes": 0,
            "textures": 0,
            "images": 0
        }

        if materials:
            for mat in bpy.data.materials:
                if mat.users == 0:
                    bpy.data.materials.remove(mat)
                    removed["materials"] += 1

        if meshes:
            for mesh in bpy.data.meshes:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
                    removed["meshes"] += 1

        if textures:
            for tex in bpy.data.textures:
                if tex.users == 0:
                    bpy.data.textures.remove(tex)
                    removed["textures"] += 1

        if images:
            for img in bpy.data.images:
                if img.users == 0:
                    bpy.data.images.remove(img)
                    removed["images"] += 1

        return {
            "success": True,
            "removed": removed
        }

    # =========================================================================
    # Geometry Nodes Tools
    # =========================================================================

    def add_geometry_nodes_modifier(
        self,
        object_name: str,
        modifier_name: Optional[str] = None
    ) -> dict:
        """Add a Geometry Nodes modifier to an object."""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        if obj.type != 'MESH':
            raise ValueError(f"Object must be a mesh, got: {obj.type}")

        # Create new geometry node tree
        node_tree = bpy.data.node_groups.new(
            name=modifier_name or f"{object_name}_GeoNodes",
            type='GeometryNodeTree'
        )

        # Add modifier
        modifier = obj.modifiers.new(
            name=modifier_name or "GeometryNodes",
            type='NODES'
        )
        modifier.node_group = node_tree

        # Setup basic node structure
        self._setup_basic_geo_nodes(node_tree)

        return {
            "success": True,
            "object": object_name,
            "modifier": modifier.name,
            "node_tree": node_tree.name
        }

    def _setup_basic_geo_nodes(self, node_tree):
        """Setup basic Geometry Nodes structure."""
        nodes = node_tree.nodes
        links = node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create Group Input
        input_node = nodes.new('NodeGroupInput')
        input_node.location = (-400, 0)

        # Create Group Output
        output_node = nodes.new('NodeGroupOutput')
        output_node.location = (400, 0)

        # Add socket to input
        node_tree.inputs.new('NodeSocketGeometry', 'Geometry')
        node_tree.outputs.new('NodeSocketGeometry', 'Geometry')

        # Link
        links.new(input_node.outputs[0], output_node.inputs[0])

    def geo_nodes_subdivide(
        self,
        object_name: str,
        levels: int = 2
    ) -> dict:
        """Add subdivision to object using Geometry Nodes."""
        result = self.add_geometry_nodes_modifier(object_name)
        obj = bpy.data.objects.get(object_name)
        modifier = obj.modifiers.get(result["modifier"])
        node_tree = modifier.node_group

        nodes = node_tree.nodes
        links = node_tree.links

        # Add Subdivide Mesh node
        sub_node = nodes.new('GeometryNodeSubdivideMesh')
        sub_node.location = (0, 0)
        sub_node.inputs['Levels'].default_value = levels

        # Reconnect
        input_node = nodes.get('Group Input')
        output_node = nodes.get('Group Output')

        links.new(input_node.outputs[0], sub_node.inputs[0])
        links.new(sub_node.outputs[0], output_node.inputs[0])

        return {
            "success": True,
            "object": object_name,
            "subdivision_levels": levels
        }

    def geo_nodes_instance_on_points(
        self,
        object_name: str,
        instance_object: str,
        count: int = 100,
        distribution: str = "random"
    ) -> dict:
        """Instance objects on points using Geometry Nodes."""
        obj = bpy.data.objects.get(object_name)
        instance_obj = bpy.data.objects.get(instance_object)

        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        if not instance_obj:
            raise ValueError(f"Instance object not found: {instance_object}")

        result = self.add_geometry_nodes_modifier(object_name, "InstanceOnPoints")
        modifier = obj.modifiers.get(result["modifier"])
        node_tree = modifier.node_group

        nodes = node_tree.nodes
        links = node_tree.links

        # Add Distribute Points on Faces
        dist_node = nodes.new('GeometryNodeDistributePointsOnFaces')
        dist_node.location = (-200, 0)
        dist_node.inputs['Density Max'].default_value = count

        # Add Instance on Points
        inst_node = nodes.new('GeometryNodeInstanceOnPoints')
        inst_node.location = (0, 0)
        inst_node.inputs['Instance'].default_value = instance_obj

        # Reconnect
        input_node = nodes.get('Group Input')
        output_node = nodes.get('Group Output')

        links.new(input_node.outputs[0], dist_node.inputs[0])
        links.new(dist_node.outputs[0], inst_node.inputs[0])
        links.new(inst_node.outputs[0], output_node.inputs[0])

        return {
            "success": True,
            "object": object_name,
            "instance_object": instance_object,
            "count": count
        }
