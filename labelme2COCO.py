import argparse
import json
import matplotlib.pyplot as plt
import skimage.io as io
import cv2
from labelme import utils
import numpy as np
import glob
import PIL.Image

class labelme2coco(object):
    def __init__(self,labelme_json=[],save_json_path='./new.json'):
        self.labelme_json=labelme_json #labelme file path/所有labelme的json文件路径组成的列表
        self.save_json_path=save_json_path  #new json file path: /json保存位置
        self.images=[]
        self.categories=[]
        self.annotations=[]
        self.label=[]
        self.annID=1
        self.height=0
        self.width=0

        self.save_json()

    def data_transfer(self):
        for num,json_file in enumerate(self.labelme_json):
            with open(json_file,'r') as fp:
                data = json.load(fp)  # load json file/加载Json文件
                self.images.append(self.image(data,num))
                for shapes in data['shapes']:
                    label=shapes['label'].split('_')
                    if label[1] not in self.label:
                        self.categories.append(self.categorie(label))
                        self.label.append(label[1])
                    points=shapes['points']
                    self.annotations.append(self.annotation(points,label,num))
                    self.annID+=1

    def image(self,data,num):
        image={}
        img = utils.img_b64_to_arr(data['imageData'])  # pulling original image data/解析原图片数据
        # img=io.imread(data['imagePath']) # can open iamges by path/通过图片路径打开图片
        # img = cv2.imread(data['imagePath'], 0)
        height, width = img.shape[:2]
        img = None
        image['height']=height
        image['width'] = width
        image['id']=num+1
        image['file_name'] = data['imagePath'].split('/')[-1]

        self.height=height
        self.width=width

        return image

    def categorie(self,label):
        categorie={}
        categorie['supercategory'] = label[0]
        categorie['id']=len(self.label)+1 # 0 for background class /0 默认为背景
        categorie['name'] = label[1] # main ROI head class /主要检测子类
        return categorie

    def annotation(self, points, label, num):
        annotation = {}
        annotation['segmentation'] = [list(np.asarray(points).flatten())]
        annotation['iscrowd'] = 0
        annotation['image_id'] = num + 1
        annotation['bbox'] = list(map(float, self.getbbox(points)))
        annotation['area'] = annotation['bbox'][2] * annotation['bbox'][3]
        annotation['category_id'] = self.getcatid(label)
        annotation['id'] = self.annID
        return annotation

    def getcatid(self,label):
        for categorie in self.categories:
            if label[1]==categorie['name']:
                return categorie['id']
        return -1

    def getbbox(self,points):
        # img = np.zeros([self.height,self.width],np.uint8)
        # cv2.polylines(img, [np.asarray(points)], True, 1, lineType=cv2.LINE_AA)  # 画边界线
        # cv2.fillPoly(img, [np.asarray(points)], 1)  # 画多边形 内部像素值为1
        polygons = points
        mask = self.polygons_to_mask([self.height,self.width], polygons)
        return self.mask2box(mask)

    def mask2box(self, mask):
        '''
        calculate the bbox from the mask
        Mask is a image full with 0,1 and 1 is the object
        only need to calculate the rows' number and clos'
        /从mask反算出其边框
        mask：[h,w]  0、1组成的图片
        1对应对象，只需计算1对应的行列号（左上角行列号，右下角行列号，就可以算出其边框）
        '''
        # np.where(mask==1)
        index = np.argwhere(mask == 1)
        rows = index[:, 0]
        clos = index[:, 1]
        # find left top row/clo number /解析左上角行列号
        left_top_r = np.min(rows)  # y
        left_top_c = np.min(clos)  # x

        #  find right bottom row/clo number /解析右下角行列号
        right_bottom_r = np.max(rows)
        right_bottom_c = np.max(clos)

        return [left_top_c, left_top_r, right_bottom_c-left_top_c, right_bottom_r-left_top_r]
        # [x1,y1,w,h]corresponding to COCO format bbox/[x1,y1,w,h] 对应COCO的bbox格式

    def polygons_to_mask(self,img_shape, polygons):
        mask = np.zeros(img_shape, dtype=np.uint8)
        mask = PIL.Image.fromarray(mask)
        xy = list(map(tuple, polygons))
        PIL.ImageDraw.Draw(mask).polygon(xy=xy, outline=1, fill=1)
        mask = np.array(mask, dtype=bool)
        return mask

    def data2coco(self):
        data_coco={}
        data_coco['images']=self.images
        data_coco['categories']=self.categories
        data_coco['annotations']=self.annotations
        return data_coco

    def save_json(self):
        self.data_transfer()
        self.data_coco = self.data2coco()
        # save json file/保存json文件
        json.dump(self.data_coco, open(self.save_json_path, 'w'), indent=4)  # indent=4 format setting/更加美观显示

labelme_json=glob.glob('./*.json')
# labelme_json=['./1.json']

labelme2coco(labelme_json,'./new.json')