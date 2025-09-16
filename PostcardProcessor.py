#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明信片照片处理脚本
处理包含GPS信息的JPG照片，添加白条显示拍摄信息，调整为A6尺寸
输入文件夹：Z:\PostcardPhotos
输出文件夹：Z:\PostcardAfterProcess
"""

import os
from PIL import Image, ImageDraw, ImageFont, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime

class PostcardProcessor:
    def __init__(self):
        # A6尺寸 (105mm × 148mm) 在300 DPI下的像素尺寸
        self.A6_WIDTH = 1240
        self.A6_HEIGHT = 1748
        
        # 设计参数
        self.WHITE_BAR_COLOR = (248, 246, 240)  # 温暖的米白色 #F8F6F0
        self.TEXT_COLOR = (90, 90, 90)  # 柔和的深灰色 #5A5A5A
        self.WHITE_BAR_RATIO = 0.18  # 白条高度占图片高度的比例
        
    def read_raw_file(self, file_path):
        """读取RAW文件并转换为PIL Image"""
        try:
            with rawpy.imread(file_path) as raw:
                # 使用默认参数处理RAW
                rgb = raw.postprocess()
                # 转换为PIL Image
                image = Image.fromarray(rgb)
                return image
        except Exception as e:
            print(f"读取RAW文件失败 {file_path}: {e}")
            return None
    
    def extract_exif_data(self, image_path):
        """提取EXIF数据，获取拍摄时间和GPS位置"""
        try:
            # 尝试直接从文件读取EXIF（适用于JPG）
            with Image.open(image_path) as img:
                exif_dict = img._getexif()
        except:
            # 如果是RAW文件，先转换
            if image_path.lower().endswith(('.nef', '.raw')):
                img = self.read_raw_file(image_path)
                if img:
                    exif_dict = img._getexif()
                else:
                    return None, None
            else:
                return None, None
        
        if not exif_dict:
            return None, None
        
        # 提取拍摄时间
        datetime_str = None
        location_str = None
        
        for tag, value in exif_dict.items():
            tag_name = TAGS.get(tag, tag)
            
            if tag_name == 'DateTimeOriginal':
                try:
                    datetime_obj = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    datetime_str = datetime_obj.strftime('%b %d, %Y')
                except:
                    datetime_str = value
            
            elif tag_name == 'GPSInfo':
                location_str = self.extract_gps_location(value)
        
        return datetime_str, location_str
    
    def extract_gps_location(self, gps_info):
        """从GPS EXIF数据提取位置信息"""
        try:
            # 这是一个简化版本，实际使用中可能需要更复杂的GPS解析
            # 你可能需要根据具体需求调整这部分代码
            if gps_info:
                # GPS信息解析比较复杂，这里提供一个基础框架
                # 建议使用专门的GPS解析库如 gpxpy 或手动解析
                return "拍摄地点"  # 占位符，需要实际实现GPS解析
        except:
            pass
        return None
    
    def calculate_dimensions(self, original_width, original_height):
        """计算调整后的尺寸，保持比例不裁剪"""
        # 考虑白条后的可用空间
        available_height = int(self.A6_HEIGHT * (1 - self.WHITE_BAR_RATIO))
        available_width = self.A6_WIDTH
        
        # 计算缩放比例
        width_ratio = available_width / original_width
        height_ratio = available_height / original_height
        
        # 选择较小的比例以确保图片完全适应
        scale_ratio = min(width_ratio, height_ratio)
        
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        
        return new_width, new_height
    
    def should_rotate_for_a6(self, width, height):
        """判断是否需要旋转以适应A6尺寸"""
        # A6是竖向的，如果图片是横向且旋转后更适合，则建议旋转
        if width > height:  # 横向图片
            # 计算横向和旋转后的适应度
            horizontal_ratio = min(self.A6_WIDTH / width, (self.A6_HEIGHT * 0.82) / height)
            vertical_ratio = min(self.A6_WIDTH / height, (self.A6_HEIGHT * 0.82) / width)
            
            return vertical_ratio > horizontal_ratio * 1.1  # 如果旋转后明显更好，则旋转
        
        return False
    
    def create_postcard(self, image_path, output_path):
        """处理单张照片，创建明信片效果"""
        try:
            # 读取图片
            if image_path.lower().endswith(('.nef', '.raw')):
                image = self.read_raw_file(image_path)
            else:
                image = Image.open(image_path)
            
            if not image:
                print(f"无法读取图片: {image_path}")
                return False
            
            # 提取EXIF信息
            datetime_str, location_str = self.extract_exif_data(image_path)
            
            original_width, original_height = image.size
            
            # 判断是否需要旋转
            if self.should_rotate_for_a6(original_width, original_height):
                image = image.rotate(90, expand=True)
                print(f"图片已旋转90度以适应A6尺寸")
            
            # 重新获取尺寸
            current_width, current_height = image.size
            
            # 计算调整后的图片尺寸
            new_width, new_height = self.calculate_dimensions(current_width, current_height)
            
            # 调整图片尺寸
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 创建A6画布
            canvas = Image.new('RGB', (self.A6_WIDTH, self.A6_HEIGHT), self.WHITE_BAR_COLOR)
            
            # 计算图片在画布上的位置（居中）
            x_offset = (self.A6_WIDTH - new_width) // 2
            y_offset = 0
            
            # 将图片粘贴到画布上
            canvas.paste(resized_image, (x_offset, y_offset))
            
            # 创建白条区域（在图片下方）
            white_bar_height = int(self.A6_HEIGHT * self.WHITE_BAR_RATIO)
            white_bar_y = new_height
            
            # 绘制白条
            draw = ImageDraw.Draw(canvas)
            draw.rectangle(
                [0, white_bar_y, self.A6_WIDTH, self.A6_HEIGHT],
                fill=self.WHITE_BAR_COLOR
            )
            
            # 添加文字信息
            self.add_text_info(draw, white_bar_y, white_bar_height, datetime_str, location_str)
            
            # 保存结果
            canvas.save(output_path, 'JPEG', quality=95, dpi=(300, 300))
            print(f"处理完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"处理图片失败 {image_path}: {e}")
            return False
    
    def add_text_info(self, draw, white_bar_y, white_bar_height, datetime_str, location_str):
        """在白条区域添加拍摄信息"""
        try:
            # 尝试使用系统字体，如果没有则使用默认字体
            try:
                # Windows
                font = ImageFont.truetype("arial.ttf", 32)
            except:
                try:
                    # macOS
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
                except:
                    try:
                        # Linux
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                    except:
                        # 默认字体
                        font = ImageFont.load_default()
            
            # 准备文字内容
            line1 = datetime_str if datetime_str else "2024.01.01"
            line2 = location_str if location_str else "SHENZHEN"
            
            # 计算文字位置
            margin = 40
            line_spacing = white_bar_height // 4
            
            # 第一行（日期）
            text_y1 = white_bar_y + line_spacing
            draw.text((margin, text_y1), line1, fill=self.TEXT_COLOR, font=font)
            
            # 第二行（地点）
            text_y2 = text_y1 + line_spacing
            draw.text((margin, text_y2), line2, fill=self.TEXT_COLOR, font=font)
            
        except Exception as e:
            print(f"添加文字信息失败: {e}")
    
    def process_folder(self, input_folder, output_folder):
        """处理整个文件夹"""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 支持的文件格式
        supported_formats = ('.jpg', '.jpeg', '.nef', '.raw', '.tiff', '.png')
        
        processed_count = 0
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(supported_formats):
                input_path = os.path.join(input_folder, filename)
                
                # 输出文件名
                name_without_ext = os.path.splitext(filename)[0]
                output_filename = f"{name_without_ext}_postcard.jpg"
                output_path = os.path.join(output_folder, output_filename)
                
                print(f"正在处理: {filename}")
                if self.create_postcard(input_path, output_path):
                    processed_count += 1
        
        print(f"\n处理完成！共处理了 {processed_count} 张照片")

if __name__ == "__main__":

    processor = PostcardProcessor()
    processor.process_folder(r"z:\PostcardPhotos", r"z:\PostcardAfterProcess")
