#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from tqdm import tqdm
from PIL import Image
from ..arguments import ModelParams
from ..scene.cameras import Camera
import numpy as np
from ..scene.dataset_readers import CameraInfo
# from .general_utils import PILtoTorch
from .graphics_utils import fov2focal

WARNED = False

def loadCam(args: ModelParams, id, cam_info: CameraInfo, resolution_scale):
    with Image.open(cam_info.image_path) as img:
        orig_w, orig_h = img.size

    if args.resolution in [1, 2, 4, 8]:
        resolution = round(orig_w/(resolution_scale * args.resolution)), round(orig_h/(resolution_scale * args.resolution))
    else:  # should be a type that converts to float
        if args.resolution == -1:
            if orig_w > 1600:
                global WARNED
                if not WARNED:
                    print("[ INFO ] Encountered quite large input images (>1.6K pixels width), rescaling to 1.6K.\n "
                        "If this is not desired, please explicitly specify '--resolution/-r' as 1")
                    WARNED = True
                global_down = orig_w / 1600
            else:
                global_down = 1
        else:
            global_down = orig_w / args.resolution

        scale = float(global_down) * float(resolution_scale)
        resolution = (int(orig_w / scale), int(orig_h / scale))

    return Camera(
        colmap_id=cam_info.uid,
        R=cam_info.R,
        T=cam_info.T,
        FoVx=cam_info.FovX,
        FoVy=cam_info.FovY,
        resolution=resolution,
        image_path=cam_info.image_path,
        depth_cam_path=cam_info.depth_cam_path,
        depth_est_path=cam_info.depth_est_path,
        image_name=cam_info.image_name,
        uid=id,
        data_device=args.data_device,
    )

def cameraList_from_camInfos(cam_infos, resolution_scale, args: ModelParams):
    Camera.preload = args.preload
    print("gt image preload:", Camera.preload)
    print("This would affect the time taken to load the images")
    camera_list = [loadCam(args, id, c, resolution_scale) for id, c in tqdm(enumerate(cam_infos))]

    return camera_list

def camera_to_JSON(id, camera : Camera):
    Rt = np.zeros((4, 4))
    Rt[:3, :3] = camera.R.transpose()
    Rt[:3, 3] = camera.T
    Rt[3, 3] = 1.0

    W2C = np.linalg.inv(Rt)
    pos = W2C[:3, 3]
    rot = W2C[:3, :3]
    serializable_array_2d = [x.tolist() for x in rot]
    camera_entry = {
        'id' : id,
        'img_name' : camera.image_name,
        'width' : camera.width,
        'height' : camera.height,
        'position': pos.tolist(),
        'rotation': serializable_array_2d,
        'fy' : fov2focal(camera.FovY, camera.height),
        'fx' : fov2focal(camera.FovX, camera.width)
    }
    return camera_entry
