"""
ShxGlyphViewer.py
برنامه‌ای برای مشاهده و نمایش تمام گلیف‌های موجود در فونت‌های SHX (مخصوص اتوکد)

نحوه اجرا:
1. فایل فونت SHX را در پوشه کنار برنامه قرار دهید (مانند NASKHD.SHX)
2. برنامه را با دستور زیر اجرا کنید:
   python ShxGlyphViewer.py
3. برنامه به‌طور خودکار فایل SHX را پیدا کرده و تصویر گلیف‌ها را تولید می‌کند
4. تصویر تولید شده به نام {نام_فونت}_glyphs.png ذخیره می‌شود

پیش‌نیازها:
- pip install pillow
- pip install shxparser
- pip install svgelements

برای استفاده از فایل خاص:
- فایل SHX مورد نظر را در پوشه جاری قرار دهید
- یا نام فایل را در لیست test_files در تابع main() تغییر دهید
"""

import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# ============================================
# بخش 1: وارد کردن کتابخانه‌های مورد نیاز
# ============================================

try:
    from svgelements import Arc  # برای رسم کمان‌های دقیق
except ImportError:
    print("⚠️ svgelements نصب نیست. نصب کنید: pip install svgelements")
    sys.exit(1)

try:
    from shxparser.shxparser import ShxFont, ShxFontParseError
    print("✅ ShxFont با موفقیت import شد")
except ImportError as e:
    print(f"❌ خطا در import: {e}")
    print("برای نصب: pip install shxparser")
    sys.exit(1)


# ============================================
# بخش 2: کلاس مسیر برای ذخیره داده‌های رندر شده
# ============================================

class ShxPath:
    """
    کلاس مسیر برای ذخیره‌سازی خروجی رندر shxparser
    این کلاس مشابه ShxPath اصلی در کتابخانه است اما برای رندر سفارشی طراحی شده
    """
    
    def __init__(self):
        """مقداردهی اولیه مسیر"""
        self.path = []      # لیست اصلی مسیرها
        self._x = 0         # موقعیت فعلی x
        self._y = 0         # موقعیت فعلی y
    
    def new_path(self):
        """شروع یک مسیر جدید"""
        self.path.append(None)
    
    def move(self, x, y):
        """حرکت به نقطه جدید بدون رسم خط"""
        self.path.append([x, y])
        self._x = x
        self._y = y
    
    def line(self, x0, y0, x1, y1):
        """رسم خط از نقطه (x0,y0) به (x1,y1)"""
        self.path.append([x0, y0, x1, y1])
        self._x = x1
        self._y = y1
    
    def arc(self, x0, y0, cx, cy, x1, y1):
        """رسم کمان با نقطه شروع (x0,y0)، کنترل (cx,cy) و پایان (x1,y1)"""
        self.path.append([x0, y0, cx, cy, x1, y1])
        self._x = x1
        self._y = y1
    
    def bounds(self):
        """
        محاسبه محدوده (bounding box) مسیرها
        بازگشت: (min_x, min_y, max_x, max_y) یا None در صورت عدم وجود مسیر
        """
        min_x = float("inf")
        min_y = float("inf")
        max_x = -float("inf")
        max_y = -float("inf")
        
        for p in self.path:
            if p is None:
                continue
            if len(p) >= 2:
                min_x = min(p[0], min_x)
                min_y = min(p[1], min_y)
                max_x = max(p[0], max_x)
                max_y = max(p[1], max_y)
            if len(p) >= 4:
                min_x = min(p[2], min_x)
                min_y = min(p[3], min_y)
                max_x = max(p[2], max_x)
                max_y = max(p[3], max_y)
            if len(p) >= 6:
                min_x = min(p[4], min_x)
                min_y = min(p[5], min_y)
                max_x = max(p[4], max_x)
                max_y = max(p[5], max_y)
        
        if math.isinf(min_x):
            return None
        return min_x, min_y, max_x, max_y


# ============================================
# بخش 3: تابع رسم گلیف
# ============================================

def draw_glyph(paths, glyph_size, font_size, mirror=False):
    """
    رسم یک گلیف روی تصویر با مقیاس‌بندی خودکار
    
    پارامترها:
        paths: شیء ShxPath شامل داده‌های مسیر
        glyph_size: اندازه نهایی گلیف در پیکسل
        font_size: اندازه فونت استفاده شده در رندر
        mirror: اگر True باشد، گلیف به صورت آینه‌ای (برعکس) رسم می‌شود
    
    بازگشت: تصویر PIL از گلیف رسم شده
    """
    # ایجاد تصویر سفید
    img = Image.new('RGB', (glyph_size, glyph_size), 'white')
    draw = ImageDraw.Draw(img)
    
    # ====================
    # مرحله 1: جمع‌آوری نقاط برای محاسبه محدوده
    # ====================
    all_points = []
    for p in paths.path:
        if p is None:
            continue
        if len(p) == 2:
            all_points.append((p[0], p[1]))
        elif len(p) == 4:
            all_points.append((p[0], p[1]))
            all_points.append((p[2], p[3]))
        elif len(p) == 6:
            all_points.append((p[0], p[1]))
            all_points.append((p[4], p[5]))
    
    # اگر هیچ نقطه‌ای وجود ندارد، تصویر خالی برگردان
    if not all_points:
        return img
    
    # ====================
    # مرحله 2: محاسبه bounding box
    # ====================
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)
    
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return img
    
    # ====================
    # مرحله 3: محاسبه مقیاس برای fit کردن در کادر
    # ====================
    margin = 8  # فاصله از لبه‌های کادر
    scale_x = (glyph_size - margin * 2) / width
    scale_y = (glyph_size - margin * 2) / height
    scale = min(scale_x, scale_y) * 0.9  # 0.9 برای کمی فاصله بیشتر
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # ====================
    # مرحله 4: تابع تبدیل مختصات با پشتیبانی از آینه
    # ====================
    def transform(x, y):
        """تبدیل مختصات از فضای فونت به فضای تصویر"""
        new_x = (x - center_x) * scale + glyph_size / 2
        new_y = -(y - center_y) * scale + glyph_size / 2
        
        # اگر حالت آینه فعال باشد، مختصات x را برعکس می‌کنیم
        if mirror:
            new_x = glyph_size - new_x
        
        return new_x, new_y
    
    # ====================
    # مرحله 5: رسم مسیرها با مقیاس جدید
    # ====================
    for p in paths.path:
        if p is None:
            continue
        if len(p) == 2:
            continue  # نقطه move را نادیده بگیر
        elif len(p) == 4:
            # رسم خط
            x0, y0 = transform(p[0], p[1])
            x1, y1 = transform(p[2], p[3])
            draw.line((x0, y0, x1, y1), fill="black", width=2)
        elif len(p) == 6:
            # رسم کمان با استفاده از svgelements
            x0, y0 = transform(p[0], p[1])
            cx, cy = transform(p[2], p[3])
            x1, y1 = transform(p[4], p[5])
            
            arc = Arc(start=(x0, y0), control=(cx, cy), end=(x1, y1))
            steps = 20  # تعداد تقسیمات برای نمایش کمان
            for i in range(steps):
                t1 = i / steps
                t2 = (i + 1) / steps
                p1 = arc.point(t1)
                p2 = arc.point(t2)
                draw.line(
                    (round(p1[0]), round(p1[1]), round(p2[0]), round(p2[1])),
                    fill="black",
                    width=2
                )
    
    # ====================
    # مرحله 6: رسم کادر دور گلیف
    # ====================
    draw.rectangle(
        [1, 1, glyph_size - 1, glyph_size - 1],
        outline='#dddddd',
        width=1
    )
    
    return img


# ============================================
# بخش 4: کلاس اصلی نمایشگر گلیف
# ============================================

class ShxGlyphViewer:
    """
    کلاس اصلی برای بارگذاری فونت SHX و ایجاد جدول گلیف‌ها
    """
    
    def __init__(self, shx_path, cols=20, glyph_size=80, padding=10, mirror=False):
        """
        مقداردهی اولیه نمایشگر
        
        پارامترها:
            shx_path: مسیر فایل SHX
            cols: تعداد ستون‌های جدول
            glyph_size: اندازه هر گلیف در پیکسل
            padding: فاصله بین گلیف‌ها
            mirror: اگر True باشد، گلیف‌ها به صورت آینه‌ای نمایش داده می‌شوند
        """
        self.shx_path = shx_path
        self.cols = cols
        self.glyph_size = glyph_size
        self.padding = padding
        self.cell_size = glyph_size + padding * 2
        self.font = None
        self.glyphs = []
        self.mirror = mirror  # حالت آینه‌ای
        
    def load_font(self):
        """
        بارگذاری فایل فونت SHX با استفاده از shxparser
        
        بازگشت: True در صورت موفقیت، False در صورت خطا
        """
        try:
            print(f"📂 بارگذاری فونت: {self.shx_path}")
            self.font = ShxFont(self.shx_path)
            print("✅ فونت با موفقیت بارگذاری شد")
            print(f"📋 نام فونت: {self.font.font_name}")
            print(f"📋 تعداد گلیف‌ها: {len(self.font.glyphs)}")
            print(f"📋 نوع فونت: {self.font.type}")
            print(f"📋 بالا (above): {self.font.above}")
            print(f"📋 پایین (below): {self.font.below}")
            
            if self.mirror:
                print("🔄 حالت آینه‌ای (Mirror) فعال است - گلیف‌ها برعکس نمایش داده می‌شوند")
            
            # استخراج گلیف‌ها
            self.glyphs = self.get_available_chars()
            
            if self.glyphs:
                print(f"✅ {len(self.glyphs)} گلیف معتبر پیدا شد")
                return True
            else:
                print("⚠️ هیچ گلیفی پیدا نشد")
                return False
                
        except Exception as e:
            print(f"❌ خطا در بارگذاری فونت: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_available_chars(self):
        """
        استخراج لیست کاراکترهای موجود از دیکشنری گلیف‌ها
        
        بازگشت: لیست مرتب شده از کدهای کاراکتر
        """
        chars = []
        for key in self.font.glyphs.keys():
            if isinstance(key, int):
                chars.append(key)
            elif isinstance(key, str) and len(key) == 1:
                chars.append(ord(key))
        
        # اگر گلیفی پیدا نشد، محدوده‌های استاندارد را بررسی کن
        if not chars:
            print("🔍 جستجوی کاراکترها در محدوده‌های استاندارد...")
            test_ranges = [
                (32, 127),      # ASCII
                (128, 255),     # Extended ASCII
                (0x0600, 0x06FF), # Arabic
                (0xFB50, 0xFDFF), # Arabic Extended
                (0xFE70, 0xFEFF), # Arabic Presentation
            ]
            
            for start, end in test_ranges:
                for code in range(start, end + 1):
                    if code in self.font.glyphs:
                        chars.append(code)
        
        return sorted(set(chars))
    
    def render_glyph(self, char_code):
        """
        رندر یک گلیف خاص
        
        پارامترها:
            char_code: کد یونیکد کاراکتر
        
        بازگشت: تصویر PIL از گلیف رندر شده
        """
        try:
            path = ShxPath()
            
            # تنظیم اندازه فونت
            font_size = self.glyph_size * 0.7
            if self.font.above:
                font_size = self.glyph_size * 0.7
            
            # رندر با shxparser
            self.font.render(path, chr(char_code), horizontal=True, font_size=font_size)
            
            # رسم گلیف با حالت آینه‌ای
            img = draw_glyph(path, self.glyph_size, font_size, mirror=self.mirror)
            return img
            
        except Exception as e:
            # در صورت خطا، یک علامت خطا نمایش بده
            img = Image.new('RGB', (self.glyph_size, self.glyph_size), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((self.glyph_size//2 - 5, self.glyph_size//2 - 5), "!", fill='red')
            draw.rectangle([1, 1, self.glyph_size - 1, self.glyph_size - 1], outline='#dddddd', width=1)
            return img
    
    def create_glyph_table(self):
        """
        ایجاد جدول کامل از تمام گلیف‌ها
        
        بازگشت: تصویر PIL از جدول گلیف‌ها
        """
        # بارگذاری فونت در صورت نیاز
        if not self.glyphs:
            if not self.load_font():
                return None
        
        if not self.glyphs:
            print("⚠️ هیچ گلیفی برای نمایش وجود ندارد")
            return None
        
        print(f"📊 تعداد گلیف‌ها: {len(self.glyphs)}")
        
        # محدود کردن تعداد گلیف‌ها برای جلوگیری از تصویر بسیار بزرگ
        max_glyphs = 300
        if len(self.glyphs) > max_glyphs:
            print(f"⚠️ محدود به {max_glyphs} گلیف اول")
            self.glyphs = self.glyphs[:max_glyphs]
        
        # محاسبه ابعاد جدول
        rows = math.ceil(len(self.glyphs) / self.cols)
        img_width = self.cols * self.cell_size + 20
        img_height = rows * self.cell_size + 80
        
        # ایجاد تصویر سفید
        img = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # ====================
        # رسم عنوان و اطلاعات
        # ====================
        try:
            title_font = ImageFont.truetype("arial.ttf", 14)
        except:
            title_font = ImageFont.load_default()
        
        title = f"Glyph Viewer - {os.path.basename(self.shx_path)}"
        if self.mirror:
            title += " (Mirror Mode - آینه)"
        draw.text((10, 10), title, fill='black', font=title_font)
        
        info = f"Total Glyphs: {len(self.glyphs)} | Columns: {self.cols} | Rows: {rows}"
        draw.text((10, 30), info, fill='gray', font=title_font)
        draw.line([(0, 50), (img_width, 50)], fill='gray', width=1)
        
        # ====================
        # رسم گلیف‌ها در جدول
        # ====================
        print("🎨 در حال رندر کردن گلیف‌ها...")
        for i, char_code in enumerate(self.glyphs):
            row = i // self.cols
            col = i % self.cols
            
            x = col * self.cell_size + 10
            y = row * self.cell_size + 60
            
            # رندر و قرار دادن گلیف
            glyph_img = self.render_glyph(char_code)
            img.paste(glyph_img, (x + self.padding, y + self.padding))
            
            # نمایش کد کاراکتر زیر گلیف - اندازه فونت 18
            try:
                # استفاده از فونت با سایز 18
                small_font = ImageFont.truetype("arial.ttf", 18)
            except:
                # اگر فونت arial پیدا نشد، از فونت پیش‌فرض با سایز بزرگتر استفاده کن
                try:
                    small_font = ImageFont.truetype("tahoma.ttf", 18)
                except:
                    small_font = ImageFont.load_default()
            
            code_text = f"Code: {char_code}"
            
            # محاسبه موقعیت برای وسط‌چین کردن متن زیر گلیف
            bbox = draw.textbbox((0, 0), code_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (self.cell_size - text_width) // 2
            
            draw.text(
                (text_x, y + self.glyph_size + self.padding - 2),
                code_text,
                fill='gray',
                font=small_font
            )
            
            # نمایش پیشرفت
            if (i + 1) % 50 == 0:
                print(f"   {i + 1}/{len(self.glyphs)} گلیف رندر شد")
        
        print("✅ رندر کامل شد")
        return img
    
    def save_image(self, output_path=None):
        """
        ذخیره تصویر جدول گلیف‌ها
        
        پارامترها:
            output_path: مسیر فایل خروجی (اختیاری)
        
        بازگشت: مسیر فایل ذخیره شده یا None در صورت خطا
        """
        if output_path is None:
            base_name = Path(self.shx_path).stem
            mirror_suffix = "_mirror" if self.mirror else ""
            output_path = f"{base_name}{mirror_suffix}_glyphs.png"
        
        img = self.create_glyph_table()
        if img:
            img.save(output_path)
            print(f"✅ تصویر ذخیره شد: {output_path}")
            print(f"📐 ابعاد: {img.width}x{img.height}")
            return output_path
        
        print("❌ خطا در ایجاد تصویر")
        return None
    
    def show_image(self, image_path):
        """
        نمایش تصویر تولید شده با برنامه پیش‌فرض سیستم
        
        پارامترها:
            image_path: مسیر فایل تصویر
        """
        if not os.path.exists(image_path):
            print(f"❌ فایل {image_path} یافت نشد")
            return
        
        try:
            # در ویندوز
            if sys.platform == 'win32':
                os.startfile(image_path)
            # در لینوکس
            elif sys.platform == 'linux':
                subprocess.run(['xdg-open', image_path])
            # در مک
            elif sys.platform == 'darwin':
                subprocess.run(['open', image_path])
            else:
                print(f"💡 تصویر در مسیر زیر ذخیره شده است: {os.path.abspath(image_path)}")
        except Exception as e:
            print(f"⚠️ خطا در نمایش تصویر: {e}")
            print(f"💡 تصویر در مسیر زیر ذخیره شده است: {os.path.abspath(image_path)}")


# ============================================
# بخش 5: تابع اصلی (ورودی برنامه)
# ============================================

def main():
    """
    تابع اصلی برنامه - نقطه ورود
    """
    # ====================
    # مرحله 1: پیدا کردن فایل SHX
    # ====================
    test_files = ["NASKHD.SHX", "bold.SHX", "txt.SHX", "gdt.SHX"]
    shx_file = None
    
    for f in test_files:
        if os.path.exists(f):
            shx_file = f
            break
    
    if shx_file is None:
        print("❌ هیچ فایل SHX پیدا نشد")
        print("فایل‌های موجود:")
        for f in os.listdir('.'):
            if f.lower().endswith('.shx'):
                print(f"   - {f}")
        return
    
    print(f"\n📂 بارگذاری فایل: {shx_file}")
    
    # ====================
    # مرحله 2: تنظیمات بر اساس نوع فایل
    # ====================
    if "NASKHD" in shx_file.upper():
        cols = 20
        glyph_size = 100  # بزرگتر برای فونت فارسی
        mirror = True     # فعال کردن حالت آینه‌ای برای فونت فارسی
    elif "bold" in shx_file.lower():
        cols = 15
        glyph_size = 80
        mirror = False
    else:
        cols = 20
        glyph_size = 80
        mirror = False
    
    # ====================
    # مرحله 3: ایجاد و اجرای نمایشگر
    # ====================
    viewer = ShxGlyphViewer(
        shx_file, 
        cols=cols, 
        glyph_size=glyph_size, 
        padding=10,
        mirror=mirror  # ارسال حالت آینه به کلاس
    )
    output_path = viewer.save_image()
    
    # ====================
    # مرحله 4: نمایش تصویر تولید شده
    # ====================
    if output_path:
        print("\n🖼️ نمایش تصویر...")
        viewer.show_image(output_path)


# ============================================
# اجرای برنامه در صورت اجرای مستقیم فایل
# ============================================

if __name__ == "__main__":
    main()