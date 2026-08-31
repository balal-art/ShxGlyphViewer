# ShxGlyphViewer

<div align="center">

**A Python tool to view and export all glyphs from AutoCAD SHX font files as a single PNG image table**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

</div>

---

ابزاری پایتونی برای مشاهده و استخراج تمام گلیف‌های فونت‌های SHX اتوکد به صورت یک تصویر PNG

## ✨ ویژگی‌ها

- استخراج خودکار تمام گلیف‌های فونت SHX
- تولید تصویر PNG با جدول مرتب از گلیف‌ها
- پشتیبانی از حالت آینه‌ای برای فونت‌های فارسی/عربی
- نمایش کد کاراکتر زیر هر گلیف
- بدون نیاز به نصب اتوکد

## 📋 پیش‌نیازها

- Python 3.8 یا بالاتر
- pip (مدیریت بسته‌های پایتون)

## 🚀 نصب و اجرا

نصب پیش‌نیازها:
```bash
pip install shxparser pillow svgelements
```

اجرا:
```bash
python ShxGlyphViewer.py
```
## تنظیمات

برنامه به‌صورت خودکار فایل SHX را از پوشه جاری شناسایی می‌کند.

تنظیمات قابل تغییر در تابع main():
- cols: تعداد ستون‌های جدول (پیش‌فرض: 20)
- glyph_size: اندازه هر گلیف در پیکسل (پیش‌فرض: 80-100)
- mirror: فعال‌سازی حالت آینه‌ای برای فونت‌های فارسی/عربی (True/False)
- padding: فاصله بین گلیف‌ها (پیش‌فرض: 10)

برای فونت NASKHD.SHX حالت آینه به‌صورت خودکار فعال می‌شود.

##📜 مجوز

پروژه تحت مجوز MIT منتشر شده است - استفاده آزاد در پروژه‌های شخصی و تجاری

##📞 پشتیبانی

- گزارش مشکلات: https://github.com/balal-art/ShxGlyphViewer/issues
- ایمیل: balal.art@gmail.com

**⭐اگر مفید بود، به پروژه ستاره دهید!⭐**

