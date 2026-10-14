# -*- coding: utf-8 -*-
"""
نظام إدارة السجن - نسخة RTL مع دعم صور السجناء
"""

import os
import shutil
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ==================================================
#                   الإعدادات والألوان
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
PHOTOS_DIR = os.path.join(BASE_DIR, "prisoners_photos")

COLORS = {
    "bg_main":       "#0e1116",
    "bg_panel":      "#1b2230",
    "bg_input":      "#f5f7fa",
    "fg_text":       "#e8ecf3",
    "accent":        "#3a86ff",
    "accent_hover":  "#2f6ed6",
    "success":       "#2ecc71",
    "warning":       "#f1c40f",
    "danger":        "#e74c3c",
    "tab_idle":      "#243043",
    "tab_active":    "#3a86ff",
    "tab_text":      "#ffffff",
    "photo_bg":      "#101826",
}

FONT        = ("Segoe UI", 11)
FONT_BOLD   = ("Segoe UI", 11, "bold")
FONT_TITLE  = ("Segoe UI", 16, "bold")


# ==================================================
#                   تنسيقات ttk
# ==================================================
def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TNotebook", background=COLORS["bg_main"],
                    borderwidth=0, tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
                    background=COLORS["tab_idle"],
                    foreground=COLORS["tab_text"],
                    padding=[24, 10], font=FONT_BOLD, borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["tab_active"]),
                          ("active", COLORS["accent_hover"])],
              foreground=[("selected", "#ffffff"), ("active", "#ffffff")],
              expand=[("selected", [0, 0, 0, 2])])

    style.configure("TButton", font=FONT, padding=[12, 6])

    style.configure("Accent.TButton", background=COLORS["accent"],
                    foreground="white", font=FONT_BOLD,
                    padding=[14, 7], borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_hover"])])

    style.configure("Success.TButton", background=COLORS["success"],
                    foreground="white", font=FONT_BOLD,
                    padding=[14, 7], borderwidth=0)
    style.map("Success.TButton", background=[("active", "#27ae60")])

    style.configure("Danger.TButton", background=COLORS["danger"],
                    foreground="white", font=FONT_BOLD,
                    padding=[14, 7], borderwidth=0)
    style.map("Danger.TButton", background=[("active", "#c0392b")])

    style.configure("Photo.TButton", background="#6c5ce7",
                    foreground="white", font=FONT_BOLD,
                    padding=[10, 6], borderwidth=0)
    style.map("Photo.TButton", background=[("active", "#5b4bd6")])

    style.configure("TEntry", fieldbackground=COLORS["bg_input"],
                    foreground="#000000", padding=6, font=FONT)

    style.configure("TLabelframe", background=COLORS["bg_panel"],
                    foreground=COLORS["fg_text"],
                    bordercolor=COLORS["accent"],
                    relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=COLORS["bg_panel"],
                    foreground=COLORS["accent"], font=FONT_BOLD)

    style.configure("Treeview", background="#ffffff",
                    fieldbackground="#ffffff", foreground="#000000",
                    rowheight=28, font=FONT)
    style.configure("Treeview.Heading", background=COLORS["accent"],
                    foreground="white", font=FONT_BOLD, padding=[6, 8])
    style.map("Treeview.Heading",
              background=[("active", COLORS["accent_hover"])])
    style.map("Treeview",
              background=[("selected", COLORS["accent"])],
              foreground=[("selected", "white")])


# ==================================================
#                   أدوات مساعدة
# ==================================================
def load_image(path, size=None):
    if not PIL_AVAILABLE or not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def rtl_entry(parent, textvariable, width=45):
    return ttk.Entry(parent, textvariable=textvariable,
                     width=width, justify="right")


def rtl_label(parent, text, bold=False, color=None, bg=None):
    return tk.Label(
        parent, text=text,
        font=FONT_BOLD if bold else FONT,
        bg=bg or COLORS["bg_panel"],
        fg=color or COLORS["fg_text"],
        anchor="e", justify="right",
    )


def save_photo_to_project(source_path, nid):
    """نسخ صورة السجين إلى مجلد المشروع وإرجاع المسار الجديد"""
    if not source_path or not os.path.exists(source_path):
        return ""
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    ext = os.path.splitext(source_path)[1].lower() or ".png"
    new_name = f"{nid}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    dst = os.path.join(PHOTOS_DIR, new_name)
    try:
        shutil.copy2(source_path, dst)
        return dst
    except Exception:
        return ""


# ==================================================
#                   التطبيق الرئيسي
# ==================================================
class PrisonManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام إدارة السجن")
        self.root.geometry("1300x800")
        self.root.minsize(1100, 680)
        self.root.configure(bg=COLORS["bg_main"])

        icon_path = os.path.join(IMAGES_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        setup_style(self.root)

        # ---------- قاعدة البيانات ----------
        self.conn = sqlite3.connect(os.path.join(BASE_DIR, "prison.db"))
        self.cur = self.conn.cursor()
        self.create_table()

        # صورة اختيارية للسجين الجديد (قبل الحفظ)
        self.new_photo_path = None

        # خلفية عامة
        self.bg_main = load_image(os.path.join(IMAGES_DIR, "bg_prison.png"),
                                  size=(1300, 800))

        self.build_ui()
        self.load_prisoners()

    # ==========================================
    #             قاعدة البيانات
    # ==========================================
    def create_table(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS prisoners (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                mother_name    TEXT,
                national_id    TEXT NOT NULL UNIQUE,
                birth_date     TEXT,
                address        TEXT,
                charge         TEXT,
                admission_date TEXT NOT NULL,
                cell_number    TEXT,
                photo_path     TEXT,
                release_date   TEXT,
                status         TEXT NOT NULL DEFAULT 'محبوس'
            )
        """)
        self.conn.commit()
        self.ensure_columns()

    def ensure_columns(self):
        self.cur.execute("PRAGMA table_info(prisoners)")
        existing = {row[1] for row in self.cur.fetchall()}
        needed = {
            "mother_name": "TEXT", "birth_date": "TEXT",
            "address": "TEXT", "cell_number": "TEXT",
            "photo_path": "TEXT",
        }
        for col, col_type in needed.items():
            if col not in existing:
                self.cur.execute(
                    f"ALTER TABLE prisoners ADD COLUMN {col} {col_type}"
                )
        self.conn.commit()

    # ==========================================
    #             بناء الواجهة
    # ==========================================
    def build_ui(self):
        if self.bg_main:
            self.canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.create_image(0, 0, image=self.bg_main, anchor="nw")
            self.main_container = tk.Frame(self.canvas, bg=COLORS["bg_main"])
            self.canvas.create_window(0, 0, window=self.main_container,
                                      anchor="nw", width=1300, height=800)
        else:
            self.main_container = tk.Frame(self.root, bg=COLORS["bg_main"])
            self.main_container.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_add = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.tab_active = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.tab_released = tk.Frame(self.notebook, bg=COLORS["bg_main"])

        self.notebook.add(self.tab_add, text="  ➕  تسجيل سجين جديد  ")
        self.notebook.add(self.tab_active, text="  🔒  السجناء الحاليون  ")
        self.notebook.add(self.tab_released, text="  ✅  المفرج عنهم  ")

        self.build_add_tab()
        self.build_active_tab()
        self.build_released_tab()

    def make_banner(self, parent, image_name, fallback_text, fallback_color):
        banner_img = load_image(os.path.join(IMAGES_DIR, image_name),
                                size=(1260, 110))
        if banner_img:
            holder = tk.Label(parent, image=banner_img, bd=0,
                              bg=COLORS["bg_main"])
            holder.image = banner_img
            holder.pack(fill="x", padx=0, pady=(0, 8))
        else:
            holder = tk.Label(parent, text=fallback_text,
                              font=FONT_TITLE, bg=fallback_color,
                              fg="white", pady=22, anchor="center")
            holder.pack(fill="x", padx=0, pady=(0, 8))

    # ==========================================
    #       تبويب تسجيل سجين جديد
    # ==========================================
    def build_add_tab(self):
        self.make_banner(self.tab_add, "banner_add.png",
                         "📝  تسجيل سجين جديد", COLORS["accent"])

        # حاوية أفقية: النموذج يمين، الصورة يسار (RTL)
        container = tk.Frame(self.tab_add, bg=COLORS["bg_main"])
        container.pack(fill="both", expand=True, padx=30, pady=5)

        # ---------- إطار بيانات السجين (يُلصق يميناً) ----------
        form_frame = tk.LabelFrame(
            container, text="  بيانات السجين  ",
            font=FONT_BOLD, bg=COLORS["bg_panel"], fg=COLORS["accent"],
            bd=1, relief="solid", padx=25, pady=18,
        )
        form_frame.pack(side="right", fill="both", expand=True, padx=(15, 0))

        self.var_name = tk.StringVar()
        self.var_mother = tk.StringVar()
        self.var_nid = tk.StringVar()
        self.var_birth = tk.StringVar()
        self.var_address = tk.StringVar()
        self.var_cell = tk.StringVar()
        self.var_charge = tk.StringVar()
        self.var_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        rows = [
            (" : الاسم الكامل", self.var_name),
            (" : اسم الأم ", self.var_mother),
            (" : الرقم الوطني ", self.var_nid),
            (" : مواليد السجين (YYYY-MM-DD) ", self.var_birth),
            (" : عنوان السكن ", self.var_address),
            (" : رقم الزنزانة ", self.var_cell),
            (" : التهمة ", self.var_charge),
            (" : تاريخ الدخول (YYYY-MM-DD) ", self.var_date),
        ]
        for i, (label, var) in enumerate(rows):
            rtl_entry(form_frame, var, width=45).grid(
                row=i, column=0, padx=(0, 15), pady=6, sticky="w"
            )
            rtl_label(form_frame, label, bold=True).grid(
                row=i, column=1, padx=(15, 0), pady=6, sticky="e"
            )
        form_frame.columnconfigure(0, weight=0)
        form_frame.columnconfigure(1, weight=1)

        # ---------- إطار الصورة (يُلصق يساراً) ----------
        photo_frame = tk.LabelFrame(
            container, text="  صورة السجين  ",
            font=FONT_BOLD, bg=COLORS["bg_panel"], fg=COLORS["accent"],
            bd=1, relief="solid", padx=15, pady=15,
        )
        photo_frame.pack(side="left", fill="y", padx=(0, 15))

        # مربع معاينة الصورة
        self.photo_preview = tk.Label(
            photo_frame, text="لا توجد صورة",
            bg=COLORS["photo_bg"], fg="#8a94a8",
            font=FONT, width=22, height=12,
            relief="solid", bd=1, compound="center",
        )
        self.photo_preview.pack(padx=5, pady=5)
        self.photo_preview.image = None

        # أزرار التحكم بالصورة
        photo_btns = tk.Frame(photo_frame, bg=COLORS["bg_panel"])
        photo_btns.pack(pady=8)

        ttk.Button(photo_btns, text="📷  اختيار صورة",
                   style="Photo.TButton",
                   command=self.choose_photo).pack(side="right", padx=4)
        ttk.Button(photo_btns, text="🗑  حذف",
                   style="TButton",
                   command=self.clear_photo).pack(side="right", padx=4)

        # ---------- أزرار العمليات ----------
        btns = tk.Frame(self.tab_add, bg=COLORS["bg_main"])
        btns.pack(pady=14)
        ttk.Button(btns, text="✅  تسجيل السجين",
                   style="Success.TButton",
                   command=self.add_prisoner).pack(side="right", padx=8)
        ttk.Button(btns, text="🧹  تفريغ الحقول",
                   style="TButton",
                   command=self.clear_form).pack(side="right", padx=8)

    # ==========================================
    #       تبويب السجناء الحاليين
    # ==========================================
    def build_active_tab(self):
        self.make_banner(self.tab_active, "banner_active.png",
                         "🔒  السجناء الحاليون", COLORS["tab_idle"])

        # ---------- شريط البحث ----------
        search_box = tk.LabelFrame(
            self.tab_active, text="  البحث  ",
            font=FONT_BOLD, bg=COLORS["bg_panel"], fg=COLORS["accent"],
            bd=1, relief="solid", padx=15, pady=10,
        )
        search_box.pack(fill="x", padx=15, pady=8)

        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *a: self.load_prisoners())
        self.var_search_field = tk.StringVar(value="الكل")

        ttk.Button(search_box, text="🧹  تفريغ",
                   command=lambda: self.var_search.set("")).grid(
            row=0, column=0, padx=6, pady=5)
        ttk.Combobox(search_box, textvariable=self.var_search_field,
                     width=18, state="readonly", justify="right",
                     values=["الكل", "الاسم", "الرقم الوطني", "اسم الأم",
                             "رقم الزنزانة", "التهمة", "عنوان السكن"]
                     ).grid(row=0, column=1, padx=6, pady=5)
        rtl_label(search_box,  " : حقل البحث ").grid(
            row=0, column=2, padx=6, pady=5, sticky="e")
        rtl_entry(search_box, self.var_search, width=30).grid(
            row=0, column=3, padx=6, pady=5)
        rtl_label(search_box,  " : كلمة البحث ").grid(
            row=0, column=4, padx=6, pady=5, sticky="e")

        # ---------- شريط الأزرار ----------
        actions = tk.Frame(self.tab_active, bg=COLORS["bg_main"])
        actions.pack(fill="x", padx=15, pady=4)

        ttk.Button(actions, text="🗑  إطلاق سراح المحدد",
                   style="Danger.TButton",
                   command=self.release_selected).pack(side="right", padx=5)
        ttk.Button(actions, text="✏  تعديل بيانات المحدد",
                   style="Accent.TButton",
                   command=self.open_edit_window).pack(side="right", padx=5)
        ttk.Button(actions, text="🖼  عرض الصورة",
                   style="Photo.TButton",
                   command=self.view_selected_photo).pack(side="right", padx=5)
        ttk.Button(actions, text="🔄  تحديث القائمة",
                   style="TButton",
                   command=self.load_prisoners).pack(side="right", padx=5)

        # ---------- الجدول ----------
        tree_holder = tk.Frame(self.tab_active, bg=COLORS["bg_main"])
        tree_holder.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("photo", "id", "name", "mother_name", "national_id",
                "birth_date", "address", "cell_number", "charge",
                "admission_date")
        heads = ("صورة", "الرقم", "الاسم", "اسم الأم", "الرقم الوطني",
                 "المواليد", "عنوان السكن", "رقم الزنزانة", "التهمة",
                 "تاريخ الدخول")

        self.tree = ttk.Treeview(tree_holder, columns=cols,
                                 show="headings", selectmode="browse")
        widths = {"photo": 60, "id": 55, "name": 130, "mother_name": 130,
                  "national_id": 120, "birth_date": 100, "address": 180,
                  "cell_number": 90, "charge": 130, "admission_date": 100}
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, anchor="e", width=widths[c])

        sb = ttk.Scrollbar(tree_holder, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.tree.pack(side="right", fill="both", expand=True)

        self.tree.bind("<Double-1>", lambda e: self.open_edit_window())

        self.lbl_count = tk.Label(
            self.tab_active, text="عدد السجناء الحاليين: 0",
            bg=COLORS["bg_main"], fg=COLORS["fg_text"], font=FONT_BOLD,
        )
        self.lbl_count.pack(pady=5)

    # ==========================================
    #       تبويب المفرج عنهم
    # ==========================================
    def build_released_tab(self):
        self.make_banner(self.tab_released, "banner_released.png",
                         "✅  المفرج عنهم", COLORS["success"])

        tree_holder = tk.Frame(self.tab_released, bg=COLORS["bg_main"])
        tree_holder.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("photo", "id", "name", "mother_name", "national_id",
                "birth_date", "address", "cell_number", "charge",
                "admission_date", "release_date")
        heads = ("صورة", "الرقم", "الاسم", "اسم الأم", "الرقم الوطني",
                 "المواليد", "عنوان السكن", "رقم الزنزانة", "التهمة",
                 "تاريخ الدخول", "تاريخ الإفراج")

        self.tree_rel = ttk.Treeview(tree_holder, columns=cols,
                                     show="headings", selectmode="browse")
        widths = {"photo": 60, "id": 55, "name": 120, "mother_name": 120,
                  "national_id": 110, "birth_date": 95, "address": 170,
                  "cell_number": 85, "charge": 120, "admission_date": 95,
                  "release_date": 95}
        for c, h in zip(cols, heads):
            self.tree_rel.heading(c, text=h)
            self.tree_rel.column(c, anchor="e", width=widths[c])

        sb = ttk.Scrollbar(tree_holder, orient="vertical",
                           command=self.tree_rel.yview)
        self.tree_rel.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.tree_rel.pack(side="right", fill="both", expand=True)

        # النقر المزدوج لعرض الصورة
        self.tree_rel.bind("<Double-1>", lambda e: self.view_released_photo())

    # ==========================================
    #             إدارة الصور
    # ==========================================
    def choose_photo(self):
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "تنبيه",
                "مكتبة Pillow غير مثبتة.\nثبّتها بالأمر:\npip install Pillow")
            return
        path = filedialog.askopenfilename(
            title="اختر صورة السجين",
            filetypes=[
                ("ملفات الصور", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("كل الملفات", "*.*"),
            ],
        )
        if path:
            self.new_photo_path = path
            self.update_photo_preview(path)

    def update_photo_preview(self, path):
        img = load_image(path, size=(200, 220))
        if img:
            self.photo_preview.config(image=img, text="")
            self.photo_preview.image = img
        else:
            self.photo_preview.config(image="", text="⚠ تعذّر تحميل الصورة")
            self.photo_preview.image = None

    def clear_photo(self):
        self.new_photo_path = None
        self.photo_preview.config(image="", text="لا توجد صورة")
        self.photo_preview.image = None

    def view_selected_photo(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "الرجاء تحديد سجين أولاً")
            return
        pid = self.tree.item(selected[0])["values"][0]
        self._show_photo_window(pid, "photo_path", "محبوس")

    def view_released_photo(self):
        selected = self.tree_rel.selection()
        if not selected:
            return
        pid = self.tree_rel.item(selected[0])["values"][0]
        self._show_photo_window(pid, "photo_path", "مفرج عنه")

    def _show_photo_window(self, pid, photo_col, status):
        self.cur.execute(
            f"SELECT name, {photo_col} FROM prisoners WHERE id = ?", (pid,)
        )
        row = self.cur.fetchone()
        if not row:
            messagebox.showerror("خطأ", "لم يتم العثور على السجين")
            return
        name, photo_path = row

        win = tk.Toplevel(self.root)
        win.title(f"صورة السجين: {name}")
        win.configure(bg=COLORS["bg_panel"])
        win.grab_set()
        win.transient(self.root)

        header = tk.Label(win, text=f"🖼  {name}",
                          font=FONT_TITLE, bg=COLORS["accent"],
                          fg="white", pady=12, padx=30)
        header.pack(fill="x")

        if photo_path and os.path.exists(photo_path):
            img = load_image(photo_path, size=(360, 420))
            if img:
                lbl = tk.Label(win, image=img, bg=COLORS["bg_panel"])
                lbl.image = img
                lbl.pack(padx=20, pady=20)
            else:
                tk.Label(win, text="⚠ تعذّر تحميل الصورة",
                         bg=COLORS["bg_panel"], fg=COLORS["warning"],
                         font=FONT_BOLD, padx=40, pady=40).pack()
        else:
            tk.Label(win, text="📷\nلا توجد صورة محفوظة لهذا السجين",
                     bg=COLORS["bg_panel"], fg="#8a94a8",
                     font=FONT_BOLD, padx=40, pady=40).pack()

        ttk.Button(win, text="إغلاق", style="TButton",
                   command=win.destroy).pack(pady=10)

    # ==========================================
    #             عمليات منطقية
    # ==========================================
    def add_prisoner(self):
        name = self.var_name.get().strip()
        mother = self.var_mother.get().strip()
        nid = self.var_nid.get().strip()
        birth = self.var_birth.get().strip()
        address = self.var_address.get().strip()
        cell = self.var_cell.get().strip()
        charge = self.var_charge.get().strip()
        date = self.var_date.get().strip()

        if not name or not nid:
            messagebox.showwarning("تنبيه", "الاسم والرقم الوطني حقول إلزامية")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("خطأ", "صيغة تاريخ الدخول غير صحيحة (YYYY-MM-DD)")
            return

        if birth:
            try:
                datetime.strptime(birth, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("خطأ", "صيغة تاريخ الميلاد غير صحيحة (YYYY-MM-DD)")
                return

        # حفظ الصورة في مجلد المشروع
        saved_photo = ""
        if self.new_photo_path:
            saved_photo = save_photo_to_project(self.new_photo_path, nid)
            if not saved_photo:
                messagebox.showwarning(
                    "تنبيه",
                    "تم حفظ بيانات السجين لكن تعذّر نسخ الصورة.")

        try:
            self.cur.execute(
                """INSERT INTO prisoners
                   (name, mother_name, national_id, birth_date, address,
                    cell_number, charge, admission_date, photo_path, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'محبوس')""",
                (name, mother, nid, birth, address, cell, charge,
                 date, saved_photo)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("خطأ", "هذا الرقم الوطني مسجّل مسبقاً")
            return

        messagebox.showinfo("تم بنجاح", f"تم تسجيل السجين: {name}")
        self.clear_form()
        self.load_prisoners()

    def clear_form(self):
        for v in (self.var_name, self.var_mother, self.var_nid,
                  self.var_birth, self.var_address, self.var_cell,
                  self.var_charge):
            v.set("")
        self.var_date.set(datetime.now().strftime("%Y-%m-%d"))
        self.clear_photo()

    # ---------- تعديل بيانات السجين ----------
    def open_edit_window(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "الرجاء تحديد سجين أولاً")
            return

        pid = self.tree.item(selected[0])["values"][1]  # عمود id صار ثانياً
        self.cur.execute("""
            SELECT id, name, mother_name, national_id, birth_date,
                   address, cell_number, charge, admission_date, photo_path
            FROM prisoners WHERE id = ?
        """, (pid,))
        row = self.cur.fetchone()
        if not row:
            messagebox.showerror("خطأ", "لم يتم العثور على السجين")
            return

        win = tk.Toplevel(self.root)
        win.title(f"تعديل بيانات السجين رقم {row[0]}")
        win.geometry("880x620")
        win.configure(bg=COLORS["bg_panel"])
        win.grab_set()
        win.transient(self.root)

        header = tk.Label(win, text="✏  تعديل بيانات السجين",
                          font=FONT_TITLE, bg=COLORS["accent"],
                          fg="white", pady=14)
        header.pack(fill="x")

        # حاوية أفقية
        container = tk.Frame(win, bg=COLORS["bg_panel"])
        container.pack(fill="both", expand=True, padx=15, pady=10)

        # ---------- إطار الحقول (يمين) ----------
        frame = tk.Frame(container, bg=COLORS["bg_panel"], padx=15, pady=15)
        frame.pack(side="right", fill="both", expand=True)

        v = {
            "name":    tk.StringVar(value=row[1] or ""),
            "mother":  tk.StringVar(value=row[2] or ""),
            "nid":     tk.StringVar(value=row[3] or ""),
            "birth":   tk.StringVar(value=row[4] or ""),
            "address": tk.StringVar(value=row[5] or ""),
            "cell":    tk.StringVar(value=row[6] or ""),
            "charge":  tk.StringVar(value=row[7] or ""),
            "date":    tk.StringVar(value=row[8] or ""),
        }

        fields = [
            ("الاسم الكامل :", v["name"]),
            ("اسم الأم :", v["mother"]),
            ("الرقم الوطني :", v["nid"]),
            ("مواليد السجين (YYYY-MM-DD) :", v["birth"]),
            ("عنوان السكن :", v["address"]),
            ("رقم الزنزانة :", v["cell"]),
            ("التهمة :", v["charge"]),
            ("تاريخ الدخول (YYYY-MM-DD) :", v["date"]),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Entry(frame, textvariable=var, width=38,
                      justify="right").grid(
                row=i, column=0, padx=(0, 15), pady=6, sticky="w")
            rtl_label(frame, label, bold=True, bg=COLORS["bg_panel"]).grid(
                row=i, column=1, padx=(15, 0), pady=6, sticky="e")

        # ---------- إطار الصورة (يسار) ----------
        photo_frame = tk.LabelFrame(
            container, text="  صورة السجين  ",
            font=FONT_BOLD, bg=COLORS["bg_panel"], fg=COLORS["accent"],
            bd=1, relief="solid", padx=15, pady=15,
        )
        photo_frame.pack(side="left", fill="y", padx=(15, 0))

        preview = tk.Label(
            photo_frame, text="لا توجد صورة",
            bg=COLORS["photo_bg"], fg="#8a94a8",
            font=FONT, width=20, height=11,
            relief="solid", bd=1, compound="center",
        )
        preview.pack(padx=5, pady=5)

        # مسار الصورة الحالي (يُعدّل من داخل النافذة)
        current_photo = {"path": row[9] or ""}

        def refresh_preview():
            p = current_photo["path"]
            if p and os.path.exists(p):
                img = load_image(p, size=(180, 200))
                if img:
                    preview.config(image=img, text="")
                    preview.image = img
                    return
            preview.config(image="", text="لا توجد صورة")
            preview.image = None

        refresh_preview()

        def pick_new_photo():
            if not PIL_AVAILABLE:
                messagebox.showwarning("تنبيه",
                                       "مكتبة Pillow غير مثبتة", parent=win)
                return
            path = filedialog.askopenfilename(
                parent=win, title="اختر صورة السجين",
                filetypes=[("ملفات الصور",
                            "*.png *.jpg *.jpeg *.gif *.bmp *.webp")],
            )
            if path:
                current_photo["path"] = path
                refresh_preview()

        def remove_photo():
            current_photo["path"] = ""
            refresh_preview()

        p_btns = tk.Frame(photo_frame, bg=COLORS["bg_panel"])
        p_btns.pack(pady=8)
        ttk.Button(p_btns, text="📷  تغيير",
                   style="Photo.TButton",
                   command=pick_new_photo).pack(side="right", padx=4)
        ttk.Button(p_btns, text="🗑  حذف",
                   style="TButton",
                   command=remove_photo).pack(side="right", padx=4)

        # ---------- حفظ التعديلات ----------
        def save_changes():
            name = v["name"].get().strip()
            mother = v["mother"].get().strip()
            nid = v["nid"].get().strip()
            birth = v["birth"].get().strip()
            address = v["address"].get().strip()
            cell = v["cell"].get().strip()
            charge = v["charge"].get().strip()
            date = v["date"].get().strip()

            if not name or not nid:
                messagebox.showwarning("تنبيه",
                                       "الاسم والرقم الوطني إلزاميان",
                                       parent=win)
                return

            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("خطأ",
                                     "صيغة تاريخ الدخول غير صحيحة",
                                     parent=win)
                return

            if birth:
                try:
                    datetime.strptime(birth, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("خطأ",
                                         "صيغة تاريخ الميلاد غير صحيحة",
                                         parent=win)
                    return

            # معالجة الصورة: هل تغيّرت؟
            new_path = current_photo["path"]
            old_path = row[9] or ""
            final_photo = old_path

            if new_path != old_path:
                if not new_path:
                    final_photo = ""
                else:
                    # احذف القديمة إن كانت داخل مجلد المشروع
                    if old_path and PHOTOS_DIR in old_path and os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                    # إن كانت الصورة الجديدة خارج المشروع، انسخها
                    if PHOTOS_DIR not in new_path:
                        copied = save_photo_to_project(new_path, nid)
                        final_photo = copied or new_path
                    else:
                        final_photo = new_path

            try:
                self.cur.execute("""
                    UPDATE prisoners
                    SET name=?, mother_name=?, national_id=?,
                        birth_date=?, address=?, cell_number=?,
                        charge=?, admission_date=?, photo_path=?
                    WHERE id=?
                """, (name, mother, nid, birth, address, cell, charge,
                      date, final_photo, pid))
                self.conn.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ",
                                     "الرقم الوطني مسجّل لسجين آخر",
                                     parent=win)
                return

            messagebox.showinfo("تم بنجاح",
                                "تم تحديث بيانات السجين", parent=win)
            win.destroy()
            self.load_prisoners()

        btns = tk.Frame(win, bg=COLORS["bg_panel"])
        btns.pack(pady=14)
        ttk.Button(btns, text="💾  حفظ التعديلات",
                   style="Success.TButton",
                   command=save_changes).pack(side="right", padx=8)
        ttk.Button(btns, text="❌  إلغاء",
                   style="TButton",
                   command=win.destroy).pack(side="right", padx=8)

    # ---------- الإفراج ----------
    def release_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "الرجاء تحديد سجين أولاً")
            return

        values = self.tree.item(selected[0])["values"]
        pid, name = values[1], values[2]

        if not messagebox.askyesno("تأكيد الإفراج",
                                   f"هل تريد الإفراج عن السجين:\n{name} ؟"):
            return

        today = datetime.now().strftime("%Y-%m-%d")
        self.cur.execute(
            "UPDATE prisoners SET status='مفرج عنه', release_date=? WHERE id=?",
            (today, pid)
        )
        self.conn.commit()

        messagebox.showinfo("تم الإفراج",
                            f"تم الإفراج عن {name} بتاريخ {today}")
        self.load_prisoners()

    # ---------- تحميل القوائم ----------
    def load_prisoners(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.tree_rel.get_children():
            self.tree_rel.delete(item)

        term = f"%{self.var_search.get().strip()}%"
        field = self.var_search_field.get()

        field_map = {
            "الاسم": "name", "الرقم الوطني": "national_id",
            "اسم الأم": "mother_name", "رقم الزنزانة": "cell_number",
            "التهمة": "charge", "عنوان السكن": "address",
        }

        base_cols = """id, name, mother_name, national_id, birth_date,
                       address, cell_number, charge, admission_date, photo_path"""

        if field in field_map:
            sql = f"""SELECT {base_cols} FROM prisoners
                      WHERE status='محبوس' AND {field_map[field]} LIKE ?
                      ORDER BY id DESC"""
            params = (term,)
        else:
            sql = f"""SELECT {base_cols} FROM prisoners
                      WHERE status='محبوس' AND
                      (name LIKE ? OR national_id LIKE ? OR charge LIKE ?
                       OR mother_name LIKE ? OR address LIKE ? OR cell_number LIKE ?)
                      ORDER BY id DESC"""
            params = (term,) * 6

        self.cur.execute(sql, params)
        rows = self.cur.fetchall()

        for row in rows:
            pid, name, mother, nid, birth, addr, cell, charge, adm, photo = row
            photo_marker = "🖼" if photo and os.path.exists(photo) else "—"
            self.tree.insert("", "end", values=(
                photo_marker, pid, name, mother, nid, birth, addr, cell,
                charge, adm
            ))

        self.lbl_count.config(text=f"عدد السجناء الحاليين: {len(rows)}")

        self.cur.execute("""
            SELECT id, name, mother_name, national_id, birth_date,
                   address, cell_number, charge, admission_date,
                   release_date, photo_path
            FROM prisoners
            WHERE status='مفرج عنه'
            ORDER BY release_date DESC, id DESC
        """)
        for row in self.cur.fetchall():
            pid, name, mother, nid, birth, addr, cell, charge, adm, rel, photo = row
            photo_marker = "🖼" if photo and os.path.exists(photo) else "—"
            self.tree_rel.insert("", "end", values=(
                photo_marker, pid, name, mother, nid, birth, addr, cell,
                charge, adm, rel
            ))

    # ==========================================
    def on_close(self):
        self.conn.close()
        self.root.destroy()


# ==================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PrisonManagement(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()