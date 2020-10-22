from geometry_msgs.msg import Pose
import copy
import yaml

class TopoMapGenerator():

    pose_skeleton = {
        "position": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        },
        "orientation": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "w": 1.0
        }
    }

    map_skeleton = {
        "name": "",
        "map": "",
        "pointset": "",
        "last_updated": "",
        "nodes": []
    }

    node_skeleton = {
        "name": "",
        "map": "",
        "pointset": "",
        "pose": {
            "position": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            },
            "orientation": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "w": 1.0
            }
        },
        "yaw_goal_tolerance": 6.28,
        "xy_goal_tolerance": 0.3,
        "verts": copy.deepcopy([
            {"x": 0.689999997616, "y": 0.287000000477},
            {"x": 0.287000000477, "y": 0.490000009537},
            {"x": -0.287000000477, "y": 0.490000009537},
            {"x": -0.689999997616, "y": 0.287000000477},
            {"x": -0.689999997616, "y": -0.287000000477},
            {"x": -0.287000000477, "y": -0.490000009537},
            {"x": 0.287000000477, "y": -0.490000009537},
            {"x": 0.689999997616, "y": -0.287000000477}
        ]),
        "edges": [],
        "localise_by_topic": ""
    }

    edge_skeleton = {
        "edge_id": "",
        "node": "",
        "action": "move_base",
        "top_vel": 0.55,
        "map_2d": "",
        "inflation_radius": 0.0,
        "recovery_behaviours_config": ''
    }
    
    def __init__(self, topomap_name, map_name):
        self.topomap_name = topomap_name
        self.map_name = map_name

        self.topomap = copy.deepcopy(TopoMapGenerator.map_skeleton)
        self.topomap["name"] = self.topomap_name
        self.topomap["map"] = self.map_name
        self.topomap["pointset"] = self.topomap_name

    def add_node(self, name=None, pose=None):
        node = copy.deepcopy(TopoMapGenerator.node_skeleton)

        if name is None:
            name = "WayPoint" + str(len(self.topomap["nodes"]))
        node["name"] = name
        node["map"] = self.map_name
        node["pointset"] = self.topomap_name
        if pose is not None:
            node["pose"] = copy.deepcopy(pose)

        self.topomap["nodes"].append(node)

        return name

    def add_edge(self, node1, node2, action=None):
        edge1 = copy.deepcopy(TopoMapGenerator.edge_skeleton)
        edge1["edge_id"] = node1 + "_" + node2
        edge1["node"] = node2
        edge1["map_2d"] = self.map_name
        if action is not None:
            edge1["action"] = action

        edge2 = copy.deepcopy(TopoMapGenerator.edge_skeleton)
        edge2["edge_id"] = node2 + "_" + node1
        edge2["node"] = node1
        edge2["map_2d"] = self.map_name
        if action is not None:
            edge2["action"] = action

        for i in range(len(self.topomap["nodes"])):
            if self.topomap["nodes"][i]["name"] == node1:
                self.topomap["nodes"][i]["edges"].append(edge1)
            elif self.topomap["nodes"][i]["name"] == node2:
                self.topomap["nodes"][i]["edges"].append(edge2)
        

    def save_topomap(self, path=None):
        if path is None:
            path = "generated_topomap.tmap"

        with open(path, 'w') as f:
            return yaml.dump(self.topomap, f, default_flow_style=False)
