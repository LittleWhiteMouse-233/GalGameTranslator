import os
# PIL : Python Imaging Library
from typing import Union
from PIL import Image
import re
import time
import xlrd


# 资源路径
RESOURCE_PATH = os.path.join(".", "resource")


def file2dict(filepath: str) -> dict:
    dic = dict()
    with open(filepath, 'r') as file_temporary:
        list_temporary = file_temporary.readlines()
    for each in list_temporary:
        dic[each.split(': ')[0].strip()] = each.split(': ')[1].strip()
    return dic


def file2list(filepath: str) -> list:
    lis = []
    with open(filepath, 'r') as file_temporary:
        list_temporary = file_temporary.readlines()
    for each in range(len(list_temporary)):
        lis.append(list_temporary[each].strip())
    return lis


def xls2dict(filepath: str) -> dict:
    dic = dict()
    xls = xlrd.open_workbook(filename=filepath)
    sheet = xls.sheet_by_index(0)
    for i in range(sheet.nrows):
        if i == 0:
            continue
        dic[sheet.row(i)[0].value.strip()] = sheet.row(i)[1].value.strip()
    return dic


def get_icon(filepath: str, in_resource: bool = True) -> Union[str, None]:
    filename = os.path.split(filepath)[-1]
    # 分离文件名与扩展名
    temp = os.path.splitext(filename)
    icon_filepath = os.path.join(RESOURCE_PATH, temp[0] + '.ico')
    if in_resource and os.path.exists(icon_filepath):
        return icon_filepath
    if not os.path.exists(filepath):
        return None
    # 图标大小
    size = (256, 256)
    # 打开图片并设置大小
    img = Image.open(filepath).resize(size)
    # 创建resource目录
    if not os.path.exists(RESOURCE_PATH):
        os.mkdir(RESOURCE_PATH)
    # 图标文件保存至icon目录
    img.save(icon_filepath)
    return icon_filepath


def get_resize_image(filepath: str, width: int = None, height: int = None, in_resource: bool = True) -> str:
    filename = os.path.split(filepath)[-1]
    temp = os.path.splitext(filename)
    resize_filepath = os.path.join(RESOURCE_PATH, temp[0] + "_resize" + temp[1])
    if in_resource and os.path.exists(resize_filepath):
        return resize_filepath
    if not os.path.exists(filepath):
        raise FileNotFoundError
    img = Image.open(filepath)
    img_size = img.size
    if not width and not height:
        new_img_size = img_size
    elif width and not height:
        new_img_size = (width, int(img_size[1]*width/img_size[0]))
    elif not width and height:
        new_img_size = (int(img_size[0]*height/img_size[1]), height)
    else:
        new_img_size = (width, height)
    img = img.resize(new_img_size)
    # 创建resource目录
    if not os.path.exists(RESOURCE_PATH):
        os.mkdir(RESOURCE_PATH)
    img.save(resize_filepath)
    return resize_filepath


def get_time() -> str:
    return time.strftime('%H:%M:%S')


def in_english(string: str) -> bool:
    ss = re.search(r'[a-z_\-]*', string)
    return (ss.end() - ss.start()) == len(string)


def remove_char(string: str, character: str) -> str:
    return re.sub(character, ' ', string)


if __name__ == "__main__":
    print(get_icon("cat_icon.png"))
