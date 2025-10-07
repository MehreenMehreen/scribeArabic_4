from svgpathtools import Path, Line
from scipy.interpolate import griddata
import numpy as np
import cv2
import sys
sys.path.append('../../coords/')
import points
import torch
import math

def generate_offset_mapping(img, ts, path, offset_1, offset_2, max_min = None, cube_size = None):
    # cube_size = 80

    offset_1_pts = []
    offset_2_pts = []
    # for t in ts:
    for i in range(len(ts)):
        t = ts[i]
        pt = path.point(t)

        norm = None
        if i == 0:
            norm = normal(pt, path.point(ts[i+1]))
            norm = norm / dis(complex(0,0), norm)
        elif i == len(ts)-1:
            norm = normal(path.point(ts[i-1]), pt)
            norm = norm / dis(complex(0,0), norm)
        else:
            norm1 = normal(path.point(ts[i-1]), pt)
            norm1 = norm1 / dis(complex(0,0), norm1)
            norm2 = normal(pt, path.point(ts[i+1]))
            norm2 = norm2 / dis(complex(0,0), norm2)

            norm = (norm1 + norm2)/2
            norm = norm / dis(complex(0,0), norm)

        offset_vector1 = offset_1 * norm
        offset_vector2 = offset_2 * norm

        pt1 = pt + offset_vector1
        pt2 = pt + offset_vector2

        offset_1_pts.append(complexToNpPt(pt1))
        offset_2_pts.append(complexToNpPt(pt2))

    offset_1_pts = np.array(offset_1_pts)
    offset_2_pts = np.array(offset_2_pts)

    h,w = img.shape[:2]

    offset_source2 = np.array([(cube_size*i, 0) for i in range(len(offset_1_pts))], dtype=np.float32)
    offset_source1 = np.array([(cube_size*i, cube_size) for i in range(len(offset_2_pts))], dtype=np.float32)

    offset_source1 = offset_source1[::-1]
    offset_source2 = offset_source2[::-1]

    source = np.concatenate([offset_source1, offset_source2])
    destination = np.concatenate([offset_1_pts, offset_2_pts])

    source = source[:,::-1]
    destination = destination[:,::-1]

    n_w = int(offset_source2[:,0].max())
    n_h = int(cube_size)

    grid_x, grid_y = np.mgrid[0:n_h, 0:n_w]

    grid_z = griddata(source, destination, (grid_x, grid_y), method='cubic')
    map_x = np.append([], [ar[:,1] for ar in grid_z]).reshape(n_h,n_w)
    map_y = np.append([], [ar[:,0] for ar in grid_z]).reshape(n_h,n_w)
    map_x_32 = map_x.astype('float32')
    map_y_32 = map_y.astype('float32')

    rectified_to_warped_x = map_x_32
    rectified_to_warped_y = map_y_32

    grid_x, grid_y = np.mgrid[0:h, 0:w]
    grid_z = griddata(source, destination, (grid_x, grid_y), method='cubic')
    map_x = np.append([], [ar[:,1] for ar in grid_z]).reshape(h,w)
    map_y = np.append([], [ar[:,0] for ar in grid_z]).reshape(h,w)
    map_x_32 = map_x.astype('float32')
    map_y_32 = map_y.astype('float32')

    warped_to_rectified_x = map_x_32
    warped_to_rectified_y = map_y_32

    return rectified_to_warped_x, rectified_to_warped_y, warped_to_rectified_x, warped_to_rectified_y, max_min


def dis(pt1, pt2):
    a = (pt1.real - pt2.real)**2
    b = (pt1.imag - pt2.imag)**2
    return np.sqrt(a+b)

def complexToNpPt(pt):
    return np.array([pt.real, pt.imag], dtype=np.float32)

def normal(pt1, pt2):
    dif = pt1 - pt2
    return complex(-dif.imag, dif.real)

def find_t_spacing(path, cube_size):

    
    l = path.length()
    error = 0.01
    init_step_size = cube_size / l

    last_t = 0
    cur_t = 0
    pts = []
    ts = [0]
    pts.append(complexToNpPt(path.point(cur_t)))
    path_lookup = {}
    for target in np.arange(cube_size, int(l), cube_size):
        step_size = init_step_size
        for i in range(1000):
            cur_length = dis(path.point(last_t), path.point(cur_t))
            if np.abs(cur_length - cube_size) < error:
                break

            step_t = min(cur_t + step_size, 1.0)
            step_l = dis(path.point(last_t), path.point(step_t))

            if np.abs(step_l - cube_size) < np.abs(cur_length - cube_size):
                cur_t = step_t
                continue

            step_t = max(cur_t - step_size, 0.0)
            step_t = max(step_t, last_t)
            step_t = max(step_t, 1.0)

            step_l = dis(path.point(last_t), path.point(step_t))

            if np.abs(step_l - cube_size) < np.abs(cur_length - cube_size):
                cur_t = step_t
                continue

            step_size = step_size / 2.0

        last_t = cur_t

        ts.append(cur_t)
        pts.append(complexToNpPt(path.point(cur_t)))

    pts = np.array(pts)

    return ts


def remap_with_grid_sample(input_image, map_x, map_y, padding, img_tensor=None, device="cuda"):

    
    
    reshaped = False
    H, W = input_image.shape[:2]
    
    if len(input_image.shape) == 2:
        #print('reshaping', input_image.shape)
        input_image = input_image.reshape(H, W, 1)
        reshaped = True
        
    if img_tensor is None:
        # Convert input image to PyTorch tensor in NCHW format and normalize to [0, 1]
        img_tensor = torch.from_numpy(input_image).permute(2, 0, 1).unsqueeze(0).float() / 255.0

        img_tensor = img_tensor.to(device)
    
    #print(input_image.shape, map_x.shape)

    # Convert map_x and map_y to normalized coordinates in the range [-1, 1]
    norm_map_x = (torch.from_numpy(map_x.copy()).float() / (W - 1)) * 2 - 1
    norm_map_y = (torch.from_numpy(map_y.copy()).float() / (H - 1)) * 2 - 1 
    
    
    # Stack normalized coordinates to create a grid of shape (1, H, W, 2)
    grid = torch.stack((norm_map_x, norm_map_y), dim=-1).unsqueeze(0)

    # Ensure grid is on the same device as the input tensor (e.g., GPU if available)
    grid = grid.to(img_tensor.device)

    # Apply grid_sample to perform the remap operation
    output_tensor = torch.nn.functional.grid_sample(img_tensor, grid, mode='bilinear', 
                                                    padding_mode=padding, align_corners=True)
    
    
    # Convert back to NumPy and scale back to [0, 255]
    output_image = (output_tensor.squeeze(dim=0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
    if reshaped:
        output_image = output_image[:, :, 0]
    return output_image


def generate_offset_mapping_1(img, ts, path, offset_1, offset_2, 
                              cube_size = None):


    offset_1_pts = []
    offset_2_pts = []
    # for t in ts:
    for i in range(len(ts)):
        t = ts[i]
        pt = path.point(t)

        norm = None
        if i == 0:
            norm = normal(pt, path.point(ts[i+1]))
            norm = norm / dis(complex(0,0), norm)
        elif i == len(ts)-1:
            norm = normal(path.point(ts[i-1]), pt)
            norm = norm / dis(complex(0,0), norm)
        else:
            norm1 = normal(path.point(ts[i-1]), pt)
            norm1 = norm1 / dis(complex(0,0), norm1)
            norm2 = normal(pt, path.point(ts[i+1]))
            norm2 = norm2 / dis(complex(0,0), norm2)

            norm = (norm1 + norm2)/2
            norm = norm / dis(complex(0,0), norm)

        offset_vector1 = offset_1 * norm
        offset_vector2 = offset_2 * norm

        pt1 = pt + offset_vector1
        pt2 = pt + offset_vector2

        offset_1_pts.append(complexToNpPt(pt1))
        offset_2_pts.append(complexToNpPt(pt2))

    offset_1_pts = np.array(offset_1_pts)
    offset_2_pts = np.array(offset_2_pts)

    h,w = img.shape[:2]

    
    offset_source2 = np.array([(cube_size*i, 0) for i in range(len(offset_1_pts))], dtype=np.float32)
    offset_source1 = np.array([(cube_size*i, cube_size) for i in range(len(offset_2_pts))], dtype=np.float32)

    offset_source1 = offset_source1[::-1]
    offset_source2 = offset_source2[::-1]

    source = np.concatenate([offset_source1, offset_source2])
    destination = np.concatenate([offset_1_pts, offset_2_pts])

    source = source[:,::-1]
    destination = destination[:,::-1]

    n_w = int(offset_source2[:,0].max())
    n_h = int(cube_size)

    grid_x, grid_y = np.mgrid[0:n_h, 0:n_w]

    
    grid_z = griddata(source, destination, (grid_x, grid_y), method='cubic')
    map_x = np.append([], [ar[:,1] for ar in grid_z]).reshape(n_h,n_w)
    map_y = np.append([], [ar[:,0] for ar in grid_z]).reshape(n_h,n_w)
    map_x_32 = map_x.astype('float32')
    map_y_32 = map_y.astype('float32')

    rectified_to_warped_x = map_x_32
    rectified_to_warped_y = map_y_32

    return rectified_to_warped_x, rectified_to_warped_y


def get_warped_images(img, polygon_list, baseline_list, target_height=60, is_vertical=False, 
                      device="cuda"):
    
 
    num_lines = len(polygon_list)    
    all_lines = ""
        
    warped_list = []
    region_output_data = []
    
    for ind in range(len(polygon_list)):

        line_mask = extract_region_mask(img, polygon_list[ind])
 
 
        summed_axis0 = (line_mask.astype(float) / 255).sum(axis=0)
        avg_height0 = np.median(summed_axis0[summed_axis0 != 0])
        summed_axis1 = (line_mask.astype(float) / 255).sum(axis=1)
        avg_height1 = np.median(summed_axis1[summed_axis1 != 0])
        
        if is_vertical:
            avg_height = avg_height1
        else:
            avg_height = avg_height0

            
        target_step_size = avg_height*1.1

        
        paths = []
        for i in range(len(baseline_list[ind])-1):
            i_1 = i+1

            p1 = baseline_list[ind][i]
            p2 = baseline_list[ind][i_1]

            p1_c = complex(*p1)
            p2_c = complex(*p2)

            paths.append(Line(p1_c, p2_c))

        if len(paths) == 0:
            continue
            
        #try:
        if True:
            # Add a bit on the end
            tan = paths[-1].unit_tangent(1.0)
            p3_c = p2_c + target_step_size * tan
            paths.append(Line(p2_c, p3_c))

            path = Path(*paths)

            # n_w is Normalized width
            n_w = target_height*path.length()/target_step_size
            ts = np.arange(0, 1, target_height/float(n_w))

            (rectified_to_warped_x, 
             rectified_to_warped_y) = generate_offset_mapping_1(img, ts, path, target_step_size/2, 
                                                                -target_step_size/2, 
                                                                cube_size=target_height)

            rectified_to_warped_x = rectified_to_warped_x[::-1,::-1]
            rectified_to_warped_y = rectified_to_warped_y[::-1,::-1]

            
            warped = cv2.remap(img, rectified_to_warped_x, rectified_to_warped_y, cv2.INTER_CUBIC, borderValue=(255,255,255))
            warped_list.append(warped)

    return warped_list  
    
    
def extract_region_mask(img, bounding_poly):
    pts = np.array(bounding_poly, np.int32)

    #http://stackoverflow.com/a/15343106/3479446
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    roi_corners = np.array([pts], dtype=np.int32)

    ignore_mask_color = (255,)
    cv2.fillPoly(mask, roi_corners, ignore_mask_color, lineType=cv2.LINE_8)
    return mask



# First argument ignored if third argument is given
def get_line_image(polygon_flat_list, img, polygon_pts=None, target_height=60, 
                   top_down=True, upside_down=False):
    if polygon_pts is None:
        polygon_pts = points.list_to_xy(polygon_flat_list)
    baseline, is_vertical = points.get_baseline_main(polygon_pts, top_down=top_down, upside_down=upside_down)
          
    line_img = get_warped_images(img, [polygon_pts], [baseline], target_height=target_height,
                                 is_vertical=is_vertical)
    if len(line_img) > 0:
        return line_img[0]
    return None
    
