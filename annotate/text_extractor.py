import copy
from PIL import Image, ImageDraw
import os
import json
import numpy as np
import math

THRESHOLD_PERCENT_AREA = 0.80
REGION_HEADER = "Region_header"
REGION_FOOTER = "Region_footer"
REGION_MAIN = "Region_main" # We don't expect this to appear in JSON...We'll assume that whatever is not marked comes here
REGION_TAGS = [REGION_HEADER, REGION_FOOTER]
REGION_ORDER = [REGION_HEADER, REGION_MAIN, REGION_FOOTER]
ORIENT_TOP_BOTTOM_TAG = "Orient_top_bottom"
ORIENT_BOTTOM_TOP_TAG = "Orient_bottom_top"
ORIENT_UPSIDE_DOWN_TAG = "Orient_upside_down"
MIN_POLY_PTS = 3
TAG_KEY = "tags"

# Polygon helper routines
class ScribeArabicPolygon:
    def __init__(self, flat_list = None, tuple_list=None):
        self.flat_list = None
        self.tuple_list = None
        
        if flat_list is not None:
            self.flat_list = flat_list
            self.tuple_list = self.list_to_xy(flat_list)
        
        if tuple_list is not None:
            self.tuple_list = tuple_list
            self.flat_list = self.xy_to_list(tuple_list)
        self.angle = None
        self.is_vertical = None
        
    def to_dict(self):
        return {"tuple_list": self.tuple_list}
            
    def xy_to_list(self, tuples_list):     
        flat_list = [x for pair in tuples_list for x in pair]
        return flat_list
    
    def list_to_xy(self, coord_list):
        xy_list = []
        for ind in range(0, len(coord_list), 2):
            xy_list.append((coord_list[ind], coord_list[ind+1]))
        return xy_list

    def get_max_min_polygon(self, polygon=None):
        if polygon is None:
            polygon = self.tuple_list
            
        x_list = [x[0] for x in polygon]
        y_list = [y[1] for y in polygon]
        return min(x_list), min(y_list), max(x_list), max(y_list)    


    def percent_intersection(self, poly1, poly2=None): 
        if type(poly1) == ScribeArabicPolygon:
            poly1 = poly1.tuple_list
        if type(poly2) == ScribeArabicPolygon:
            poly2 = poly2.tuple_list
            
        if poly2 is None:
            poly2 = self.tuple_list
        # Determine size
        [minX1, minY1, maxX1, maxY1] = self.get_max_min_polygon(poly1)
        [minX2, minY2, maxX2, maxY2] = self.get_max_min_polygon(poly2)
        
        if maxX1 < minX2 or maxX2 < minX1:
            return 0, 0, 0  # no horizontal overlap
        
        # Check vertical separation
        if maxY1 < minY2 or maxY2 < minY1:
            return 0, 0, 0 # no vertical overlap
        
        # For now...quick and dirty for size
        size = [int(max(maxX1, maxX2)), int(max(maxY1, maxY2))]
        
        im1 = Image.new(mode="1", size=size)
        draw1 = ImageDraw.Draw(im1)    
        draw1.polygon(poly1, fill=1)
        im2 = Image.new(mode="1", size=size)    
        draw2 = ImageDraw.Draw(im2)
        draw2.polygon(poly2, fill=1)   
        mask1 = np.asarray(im1, dtype=bool)
        mask2 = np.asarray(im2, dtype=bool)
        intersection_mask = mask1 & mask2
        #plt.imshow(intersection)
        intersection_area = intersection_mask.sum()    
        percent1 = intersection_area / mask1.sum()
        percent2 = intersection_area / mask2.sum()
        return intersection_area, percent1, percent2
    
    def polygon_orientation(self, points=None):
        if points is None:
            points = self.tuple_list
            
        n = len(points)
        mean_x = sum(p[0] for p in points) / n
        mean_y = sum(p[1] for p in points) / n

        Sxx = Syy = Sxy = 0
        for x, y in points:
            dx = x - mean_x
            dy = y - mean_y
            Sxx += dx * dx
            Syy += dy * dy
            Sxy += dx * dy

        angle = 0.5 * math.atan2(2 * Sxy, Sxx - Syy)
        return math.degrees(angle)
    
    def is_near_vertical(self, thresh=15):
        if self.is_vertical is not None:
            return self.is_vertical
        
        if self.angle is None:
            self.angle = self.polygon_orientation(self.tuple_list)
            
        if abs(self.angle) <= 90 + thresh and abs(self.angle) >= 90 - thresh:
            self.is_vertical = True
            return True
        self.is_vertical = False
        return False
    
    def get_center_poly(self):
        center = np.mean(self.tuple_list, axis=0)
        return center
    
    def get_x_y(self):
        x_list = [x[0] for x in self.tuple_list]
        y_list = [y[1] for y in self.tuple_list]
        return x_list, y_list
    
    
        # num_pts is number of points on baseline to get
    def get_baseline_regression(self, poly_pts, num_pts=10, deg=1):
        if len(poly_pts) <= 4:
            deg = 1
        x, y = self.get_x_y()
        model = (np.polyfit(x, y, deg))
        p = np.poly1d(model)
        # get the x against which we want y
        x1, y1, x2, y2 = self.get_max_min_polygon(poly_pts)
        num_pts = min(num_pts, x2-x1+1)
        num_pts = int(num_pts)
        x = np.linspace(x1, x2, num_pts, endpoint=True, dtype=int)
        y = p(x)
        baseline = [(a, b) for a,b in zip(x, y)]
        return baseline
    
        # assuming poly_pts is a list of (x,y) tuples
    # This will add more points by interpolating between two points
    def expand_poly(self, poly_pts, min_x_increment=10):
        poly_pts = np.array(poly_pts).astype(int)
        new_poly = []
        #    for ind, (curr, nxt) in enumerate(zip(poly_pts[:-1], poly_pts[1:])):

        for ind, curr in enumerate(poly_pts):
            nxt = poly_pts[(ind+1)%len(poly_pts)]
            if np.abs(nxt[0] - curr[0]) < min_x_increment:
                new_poly.append(curr)
                new_poly.append(nxt)
                continue
            x1, x2 = curr[0], nxt[0]
            y1, y2 = curr[1], nxt[1]
            new_poly.append(curr)
            increment = -1*min_x_increment if nxt[0] < curr[0] else min_x_increment
            for x in range(curr[0]+1, nxt[0], increment):
                slope = float(y2-y1)/(x2-x1)
                y = slope*(x - x2) + y2
                new_poly.append((x, y))
            new_poly.append(nxt)
        return new_poly
    
    
        # Chunks_len ignored if chunk_len_auto is True
    def get_baseline_chunks(self, poly_pts, chunks_len=300, chunk_len_auto=True):
        
        
        baseline = []
        poly_pts = self.expand_poly(poly_pts)
        p = np.array(poly_pts)

        max_x, max_y = np.max(p, 0)
        min_x, min_y = np.min(p, 0)

        # Decide chunks_len
        if chunk_len_auto:
            if (len(poly_pts) >= 250):
                total_chunks = 5
            else:
                total_chunks = int(np.ceil(len(poly_pts)/50))
            chunks_len = int((max_x-min_x)/total_chunks)
        else:
            total_chunks = int((max_x-min_x)/chunks_len)

        #print('expanded len', len(poly_pts), 'total chunks', total_chunks)
        for i in range(1, total_chunks+1):
            p1 = [pt for pt in p if (pt[0]-min_x)>=(i-1)*chunks_len and (pt[0]-min_x)<i*chunks_len]
            #print(p1)
            if i == total_chunks:
                p1 = [pt for pt in p if (pt[0] - min_x)>=(i-1)*chunks_len]
            b = self.get_baseline_regression(p1, num_pts=12)

            # Points are in ascending order (increasing x - left to right) 
            if len(baseline) != 0:
                # This will smooth out the line
                # Get rid of last 4 points and connect the point with next 4 points
                baseline = baseline[:-4]
                baseline.extend(b[4:])
                if i == total_chunks:
                    baseline.extend(b[-1:])
            else:
                baseline = b

        # Make sure baseline does not repeat

        prev_pt = baseline[0]
        baseline_clean = [prev_pt]
        for b in baseline[1:]:
            if b != prev_pt:
                baseline_clean.append(b)
                prev_pt = b
        return baseline_clean

    
    
        # Takes care of vertically oriented text as well as bottom up/top down + upside down text
    def get_baseline(self, right_to_left=True, top_down=True, upside_down=False):  
        poly_points = self.tuple_list
        # First check if we have near vertical line
        is_vertical = self.is_near_vertical()
        if is_vertical:
            # First reverse coords
            poly = [(y, x) for (x, y) in poly_points]
            baseline = self.get_baseline_chunks(poly)
            # reverse again
            baseline = [(x, y) for (y, x) in baseline]

        else:
            baseline = self.get_baseline_chunks(poly_points)

        if (is_vertical and top_down) or upside_down:
            baseline = baseline[::-1]    

        return baseline, is_vertical
        
# For saving to json
class myEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, bool):
            print('Wrting bool obj')
            return 1 if obj else 0        
        if isinstance(obj, ScribeArabicPolygon):
            return obj.to_dict()
        return super(NpEncoder, self).default(obj)       

# SCribeArabic text extractor
# Will read the text and tags in JSON file and sort the lines top down, right left order
# All the header regions will appeear before main text. All footer regions will appear after main text
# If multiple regions (e.g. two footer regions) they'll be sorted top to bottom, right to left order
# If a set of lines is vertical, sorting would be: first horizontal lines, then vertical right to left 

class ScribeArabicTextExtractor:
    def __init__(self, image_json=None, json_file=None):
        if image_json is None:
            assert os.path.exists(json_file)
            with open(json_file) as fin:
                image_json = json.load(fin)
        self.json_file = json_file
        self.json = copy.deepcopy(image_json)
        self.original_json = image_json
        self.region_dict = dict()
        self.line_dict = dict()
        self.region_type_dict =dict()
        self.size = [self.json['image_size']['width'], self.json['image_size']['height']]
        self.sorted_json = dict()
        
        self.init_dicts()
        self.assign_lines_to_regions()
        self.sort_all()
        self.create_sorted_json()
        
    # GEt value from json    
    def get_value(self, key, sub_key=None, default=""):
        if sub_key is None:
            if key in self.json.keys():
                return self.json[key]
        
        elif sub_key in self.json[key]:
            return self.json[key][sub_key]
        return default    
        
    # For now if there are multiple tags then first one is taken    
    def is_valid_region(self, region_key):
        
        valid = False
        # If tags don't exist empty dictionary is returned
        tag_dict = self.get_value(region_key, TAG_KEY, dict())
        coords = self.get_value(region_key, "coord", [])
        tag = ""
        types = []
        region_type = None
        if len(coords) >= MIN_POLY_PTS*2:
            for t in tag_dict:
                if t in REGION_TAGS and tag_dict[t] == 1:
                    valid = True
                    region_type = t
                    break                
     
        return valid, region_type
        
    def init_dicts(self):
        
        self.line_dict = dict()
        self.region_dict = dict()
        self.region_type_dict =dict()
        
        for line_id, line in self.json.items():
            if not line_id.startswith('line_'):
                continue
            if not "coord" in line:
                continue
            # Get the poly rep of line
            
            line_polygon = ScribeArabicPolygon(flat_list=line["coord"])
            self.json[line_id]['line_polygon'] = line_polygon
            text = self.get_value(line_id, "text", "")
            if type(text) == str and len(text) > 0 and text != "None":
                self.line_dict[line_id] = dict()
                
            
            is_valid, region_type = self.is_valid_region(line_id)
            
            if is_valid:
                self.region_dict[line_id] = {"lines": []}
                if not region_type in self.region_type_dict:
                    self.region_type_dict[region_type] = []
                
                self.region_type_dict[region_type].append(line_id)
   
    def check_tags(self, line_data):
        # To make it json readable in javascript
        upside_down = 0
        bottom_up = 0

        if not "tags" in line_data:
            return upside_down, bottom_up

        # Check if its upside down or bottom up
        if line_data["tags"].get("Orient_upside_down", 0) == 1:
            upside_down = 1
        if line_data["tags"].get("Orient_bottom_top", 0) == 1:
            bottom_up = 1

        return upside_down, bottom_up

    def assign_orientation_to_lines(self):
        for line_id in self.line_dict:
            self.json[line_id]["upside_down"], self.json[line_id]["bottom_up"]= self.check_tags(self.json[line_id])        

    def get_baselines(self):
        for line_id in self.line_dict:
            line_data = self.json[line_id]
            (self.json[line_id]['baseline'], 
             self.json[line_id]['is_vertical']) = line_data['line_polygon'].get_baseline(top_down = not line_data["bottom_up"],
                                                                                    upside_down = line_data["upside_down"] 
                                                                                    )   
            # convert to int
            self.json[line_id]['is_vertical'] = 1 if self.json[line_id]['is_vertical'] else 0
             
    # Assign is_vertical, upside_down and bottom_up to a region if two or more lines are this way 
    def assign_orientation_to_regions(self):
        # This dict will count
        field_dict = {"is_vertical": 0, "upside_down": 0, "bottom_up": 0}
        for region_id, region_data in self.region_dict.items():
            lines = region_data['lines']
             # Make a copy
            region_field_dict = {k: v for k, v in field_dict.items()}
            for l in lines:
                for k in region_field_dict:
                    if self.json[l][k] == 1:
                         region_field_dict[k] += 1
             
             
             # Assign to region
            for k, v in region_field_dict.items():
                if (v == 1 and len(region_data['lines']) == 1) or v >= 2:
                    region_data[k] = 1
                else:
                    region_data[k] = 0
             
             
    def sort_all(self):
        # This assigns orientation to each line
        self.assign_orientation_to_lines()
        
        self.get_baselines()        
        # Should call after get_baselines as get_baselines would assign is_vertical
        self.assign_orientation_to_regions()
        # Sort all region groups defined in region_type_dict
        self.sort_region_list()
        # Sort lines within a region
        self.sort_lines_in_regions()
        
        # Give all lines an order
        self.give_sorting_order_to_lines()
        
    def give_sorting_order_to_lines(self):
        line_order = []
        for region_type in REGION_ORDER:
            if not region_type in self.region_type_dict:
                continue 
            region_list = self.region_type_dict[region_type]            
            for region_id in region_list:
                
                for line_id in self.region_dict[region_id]["lines"]:
                    line_order.append(line_id)

                 # Append the region key if not already appended
                if not region_id in line_order and region_id.startswith("line_"):
                    line_order.append(region_id)
                        
        self.json["line_order"] = line_order
        
        
        
    def sort_lines_in_regions(self):
        for region_key, region_data in self.region_dict.items():
            
            # baselines are reversed so take last one
            line_starts = [self.json[line]['baseline'][-1] for line in self.region_dict[region_key]['lines']]
            if region_data["is_vertical"] == 1:
                # Sort left to right, top to bottom
                sorted_starts = sorted(enumerate(line_starts), key=lambda x: (x[1][0], x[1][1]))
            elif region_data["upside_down"] == 1:
                # Sort bottom to top, left to right
                sorted_starts = sorted(enumerate(line_starts), key=lambda x: (-x[1][1], x[1][0]))
            else:    
                # Top to bottom, right to left
                sorted_starts = sorted(enumerate(line_starts), key=lambda x: (x[1][1], -x[1][0]))
            sorted_start_ind = [x[0] for x in sorted_starts]
            sorted_lines = [self.region_dict[region_key]['lines'][ind] for ind in sorted_start_ind]
            self.region_dict[region_key]['lines'] = sorted_lines  
        
    def sort_region_list(self):
    
        for region_type, region_list in self.region_type_dict.items():
            
            if len(region_list) <= 1:
                # This would also cover the case for REGION_MAIN...this key is not in json and so 
                # has no bounded poly
                continue
 
            region_centers = [self.json[region]['line_polygon'].get_center_poly()
                              for region in region_list]
            sorted_centers = sorted(enumerate(region_centers), key=lambda x: (x[1][1], -x[1][0]))
            sorted_centers_ind = [x[0] for x in sorted_centers]               
            sorted_regions = [region_list[sorted_index] for sorted_index in sorted_centers_ind]
            # Replace region list with sorted regions
            self.region_type_dict[region_type] = sorted_regions

    def belongs_to(self, line, region):
        _, _, percent = ScribeArabicPolygon().percent_intersection(self.json[region]['line_polygon'] , 
                                                  self.json[line]['line_polygon'])

        if percent > THRESHOLD_PERCENT_AREA:
            return True    
        return False
    
    def assign_lines_to_regions(self):
        for line_key in self.line_dict:
            for region_key in self.region_dict:
                if self.belongs_to(line_key, region_key):
                    if len(self.line_dict[line_key]) != 0 :
                        print("WARNING, line already assigned a region", line_key)
                    self.line_dict[line_key] = {'assigned': True, 'region': region_key}
                    self.region_dict[region_key]['lines'].append(line_key)

                # The rest of the lines go into main_region
        self.region_dict[REGION_MAIN] = {'lines': []}
        for line, line_values in self.line_dict.items():
            if len(line_values) == 0:
                self.region_dict[REGION_MAIN]['lines'].append(line)
                # We don't have a key for this region
                self.line_dict[line] = {'assigned': True, 'region': REGION_MAIN}
        
        # REGION_MAIN also goes into type_dict
        self.region_type_dict[REGION_MAIN] = [REGION_MAIN]
        
    def create_sorted_json(self):
        self.sorted_json = dict()
        # First copy non_line data
        for key, val in self.original_json.items():
            if not key.startswith('line_'):
                self.sorted_json[key] = val
                
        for ind, line in enumerate(self.json["line_order"]):
            self.sorted_json[f"line_{ind+1}"] = self.original_json[line]
            
    def write_sorted_json(self, filename):
        with open(filename, 'w') as fout:
            json.dump(self.sorted_json, fout, indent=2, ensure_ascii=False, cls=myEncoder)
            
    def get_sorted_json(self):
        return self.sorted_json
    
    def get_text(self):
        
        text = []
        for region_type in REGION_ORDER:
            if not region_type in self.region_type_dict:
                continue 
            region_list = self.region_type_dict[region_type]            
            for region_id in region_list:
                region_text = []
                for line_id in self.region_dict[region_id]["lines"]:
                    line_text = self.json[line_id].get("text", "")
                    if len(line_text) > 0 and line_text != "None":
                        region_text.append(line_text)
                
                 # Append the region key if not already appended
                if region_id.startswith("line_") and len(self.json[region_id]['text']) > 0:
                    region_text.append(self.json[region_id]['text'])
                region_text = ' '.join(region_text)
                text.append(region_text)
                        
        return '\n'.join(text)
    
if __name__ == "__main__":    
    
    json_file = "/work/mehreen/datasets/kclds/AR55/messy_AR55/AR55_06_034_annotate_sfr.json"  
    # Can also pass a json_obj here (image_json is the constructor)...see the constructor
    extractor = ScribeArabicTextExtractor(json_file=json_file)
    
    text = extractor.get_text()
    #sorted_json = extractor.get_sorted_json()
    #extractor.write_sorted_json(json_file)

    print('type_dict', extractor.region_type_dict, '\n')
    print('region_dict', extractor.region_dict, '\n')
    print('line_dict', extractor.line_dict)
    print(text)