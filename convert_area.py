
import xml.etree.ElementTree as ET
from pyproj import Proj
import matplotlib.pyplot as plt
from geometry_msgs.msg import Pose
from topomap_generator import TopoMapGenerator


# https://www.ordnancesurvey.co.uk/documents/product-support/user-guide/os-open-roads-user-guide.pdf
roads_file = "data/OSOpenRoads_SK.gml"

gml_prefix = "{http://www.opengis.net/gml/3.2}"
os_prefix = "{http://namespaces.os.uk/product/1.0}"
road_prefix = "{http://namespaces.os.uk/Open/Roads/1.0}"
xlink_prefix = "{http://www.w3.org/1999/xlink}"
net_prefix = "{urn:x-inspire:specification:gmlas:Network:3.2}"

# area limits [upper_corner, lower_corner]
# UPPER:
# 53d14'16.8"N 0d31'27.6"W
# 53.237989, -0.524320
# LOWER: 
# 53d13'32.8"N 0d33'40.5"W
# 53.225782, -0.561247
limits = [
    [53.237989, -0.524320],
    [53.225782, -0.561247]
]

# where to center our map in UTM
center_of_map = [53.229511, -0.540325]

# string for converting from EPSG::27700 format to lat-long ?
lonlat_proj_string = "+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +datum=OSGB36 +units=m +no_defs"
utm_proj_string = "+proj={} +zone={}, +north +ellps={} +datum={} +units={} +no_defs".format(
    "utm", 30, "WGS84", "WGS84", "m")

# declare projections
lonlat_projection = Proj(lonlat_proj_string)
print(lonlat_projection)

utm_projection = Proj(utm_proj_string)
print(utm_projection)

utm_center = utm_projection(center_of_map[1], center_of_map[0])

print("Center of map UTM:", utm_center)

# tmerc to long-lat
def tmerc_to_latlon(x, y):
    lon, lat = lonlat_projection(x, y, inverse=True)
    # print("Latlong:", lat, lon)

    return lat, lon

# long-lat to utm
def latlon_to_utm(lat, lon):
    x, y = utm_projection(lon, lat)
    # print("UTM:", x, y)

    return x, y

# offset by map center
def utm_to_map(x, y):
    x -= utm_center[0]
    y -= utm_center[1]
    # print("MAP:", x, y)

    return x, y

def tmerc_to_map(x, y):
    # tmerc to long-lat
    lat, lon = tmerc_to_latlon(x, y)

    # long-lat to utm
    x, y = latlon_to_utm(lat, lon)

    # offset by map center
    return utm_to_map(x, y)


if __name__ == "__main__":    
    # read roads file
    tree = ET.parse(roads_file)
    root = tree.getroot()

    # for low_corner in root.iter("{}lowerCorner".format(gml_prefix)):
    #     _x, _y = low_corner.text.split(" ")
    #     x, y = tmerc_to_utm(float(_x), float(_y))
    #     print("Lower coord:", x, y)

    # for upp_corner in root.iter("{}upperCorner".format(gml_prefix)):
    #     _x, _y = upp_corner.text.split(" ")
    #     x, y = tmerc_to_utm(float(_x), float(_y))
    #     print("Upper coord:", x, y)

    # get all the road nodes
    nodes = {}
    for road_node in root.iter("{}RoadNode".format(road_prefix)):
        # get node position
        for pos in road_node.iter("{}pos".format(gml_prefix)):
            _x, _y = pos.text.split(" ")
            lat, lon = tmerc_to_latlon(_x, _y)

            if lon > limits[0][1] or lon < limits[1][1] or \
                lat > limits[0][0] or lat < limits[1][0]:
                # outside our limits
                # print("Point outside limits")
                pass
            else:
                x, y = utm_to_map(*latlon_to_utm(lat, lon))
                node_id = road_node.get("{}id".format(gml_prefix))
                nodes.update({
                    node_id: [x, y]
                })

            break # there is only one anyway
    
    print("Found {} nodes inside area".format(len(nodes)))
    # print(nodes)

    # get all road links
    edges = {}
    for road_link in root.iter("{}RoadLink".format(road_prefix)):
        # get start end nodes
        start_id = ""
        emd_id = ""
        for link in road_link.iter("{}startNode".format(net_prefix)):
            start_id = link.get("{}href".format(xlink_prefix)).replace("#", "")
            break  # there is only one anyway
        for link in road_link.iter("{}endNode".format(net_prefix)):
            end_id = link.get("{}href".format(xlink_prefix)).replace("#", "")
            break  # there is only one anyway

        if start_id not in nodes or end_id not in nodes:
            # outside our limits
            # print("Link outside limits")
            pass
        else:
            # get edge id 
            edge_id = road_link.get("{}id".format(gml_prefix))
            # get edge positions (intermediate points in the road)
            pos_list = []
            for posList in road_link.iter("{}posList".format(gml_prefix)):
                l = posList.text.split(" ")
                for i in range(0, len(l), 2):
                    x, y = tmerc_to_map(l[i], l[i+1])
                    pos_list.append([x, y])
                break  # there is only one anyway
            edges.update({
                edge_id: {
                    "start": start_id,
                    "end": end_id,
                    "pos_list": pos_list
                }
            })

    print("Found {} edges inside area".format(len(edges)))
    # print(edges)



    # generate ROS topological map
    node_names = {}
    gen = TopoMapGenerator("lincoln_centre", "lincoln")
    for node_id in nodes:
        pose = TopoMapGenerator.pose_skeleton
        pose["position"]["x"] = nodes[node_id][0]
        pose["position"]["y"] = nodes[node_id][1]
        node_name = gen.add_node(pose=pose)
        node_names.update({
            node_id: node_name
        })

    for edge_id in edges:
        if edges[edge_id]["start"] in node_names:
            n1 = node_names[edges[edge_id]["start"]]
            if edges[edge_id]["end"] in node_names:
                n2 = node_names[edges[edge_id]["end"]]
        
                gen.add_edge(n1, n2)

    gen.save_topomap()


    ### visualize map
    for edge_id in edges:
        x = []
        y = []
        if edges[edge_id]["start"] in nodes:
            p = nodes[edges[edge_id]["start"]]
            x.append(p[0])
            y.append(p[1])
        if edges[edge_id]["end"] in nodes:
            p = nodes[edges[edge_id]["end"]]
            x.append(p[0])
            y.append(p[1])
        plt.plot(x, y)
    plt.show()

