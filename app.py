from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import os
import json
import base64

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

print("CLIENT_ID =", os.environ.get("GOOGLE_CLIENT_ID"))
print("CLIENT_SECRET =", os.environ.get("GOOGLE_CLIENT_SECRET"))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

# ===== إعدادات رفع الملفات =====
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# إنشاء مجلد الرفع إذا لم يكن موجوداً
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """التحقق من امتداد الملف المسموح به"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ===== نهاية إعدادات رفع الملفات =====

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

def get_current_user():
    return session.get("user")

# ========================
# الصفحات الرئيسية
# ========================

@app.route("/")
def home():
    return render_template("index.html", user=get_current_user())

@app.route("/services")
def services():
    return render_template("services.html", user=get_current_user())

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", user=get_current_user())

@app.route("/contact")
def contact():
    return render_template("contact.html", user=get_current_user())

@app.route("/pricing")
def pricing():
    return render_template("pricing.html", user=get_current_user())

@app.route("/reservoir-3d")
def reservoir_3d():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("reservoir_3d.html", user=user)

# ========================
# رفع الملفات وتحليلها
# ========================

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            return render_template('upload.html', user=user, error='No file selected')
        
        file = request.files['file']
        
        # التحقق من اختيار ملف
        if file.filename == '':
            return render_template('upload.html', user=user, error='No file selected')
        
        # التحقق من نوع الملف
        if not allowed_file(file.filename):
            return render_template('upload.html', user=user, error='Only .xlsx and .xls files are allowed')
        
        # حفظ الملف
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # عرض رسالة نجاح
        return render_template('upload.html', user=user, uploaded=True, filename=filename)
    
    return render_template('upload.html', user=user)

@app.route('/analyze/<filename>')
def analyze_file(filename):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # مسار الملف
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # التحقق من وجود الملف
    if not os.path.exists(filepath):
        return render_template('upload.html', user=user, error='File not found')
    
    # قراءة الملف باستخدام Pandas
    try:
        import pandas as pd
        df = pd.read_excel(filepath)
        
        # حساب الإحصائيات الأساسية
        stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'columns_list': df.columns.tolist(),
            'oil_column': None,
            'water_column': None,
            'gas_column': None,
            'oil_stats': None
        }
        
        # البحث عن أعمدة الإنتاج
        for col in df.columns:
            col_lower = str(col).lower()
            if 'oil' in col_lower or 'نفط' in col_lower or 'انتاج' in col_lower:
                stats['oil_column'] = col
            if 'water' in col_lower or 'ماء' in col_lower:
                stats['water_column'] = col
            if 'gas' in col_lower or 'غاز' in col_lower:
                stats['gas_column'] = col
        
        # حساب إحصائيات النفط إذا وجد العمود
        if stats['oil_column'] and stats['oil_column'] in df.columns:
            oil_data = df[stats['oil_column']].dropna()
            if len(oil_data) > 0:
                stats['oil_stats'] = {
                    'avg': oil_data.mean(),
                    'max': oil_data.max(),
                    'min': oil_data.min(),
                    'sum': oil_data.sum()
                }
        
        # عرض أول 10 صفوف
        preview = df.head(10).to_html(classes='table table-striped')
        
        return render_template('analysis.html', 
                               user=user, 
                               filename=filename,
                               stats=stats,
                               preview=preview)
    
    except Exception as e:
        return render_template('upload.html', user=user, error=f'Error reading file: {str(e)}')

# ========================
# الاشتراك والدفع
# ========================

@app.route("/subscribe/<plan>")
def subscribe(plan):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    plans = {
        "starter": {"name": "Starter", "price": "99"},
        "pro": {"name": "Pro", "price": "499"}
    }
    plan_data = plans.get(plan, plans["pro"])
    return render_template("subscribe.html", user=get_current_user(), 
                          plan=plan_data["name"], price=plan_data["price"])

# ========================
# المصادقة (Google OAuth)
# ========================

@app.route("/login")
def login():
    print("REDIRECT URI =", url_for("auth_callback", _external=True))
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    # الحصول على الـ token
    token = google.authorize_access_token()
    
    # محاولة استخراج معلومات المستخدم بطرق متعددة
    user_info = None
    
    # الطريقة 1: من userinfo
    if token.get("userinfo"):
        user_info = token.get("userinfo")
    
    # الطريقة 2: من id_token
    if not user_info and token.get("id_token"):
        try:
            id_token = token["id_token"]
            # فك الـ payload من id_token
            payload = id_token.split('.')[1]
            # إضافة padding
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            user_data = json.loads(decoded)
            user_info = {
                "name": user_data.get("name", "User"),
                "email": user_data.get("email", "user@example.com"),
                "picture": user_data.get("picture", "")
            }
        except Exception as e:
            print("Error decoding id_token:", e)
    
    # الطريقة 3: استخدام google.get
    if not user_info:
        try:
            resp = google.get("userinfo")
            user_info = resp.json()
        except Exception as e:
            print("Error getting userinfo:", e)
    
    # الطريقة 4: قيم افتراضية
    if not user_info:
        user_info = {
            "name": "User",
            "email": "user@example.com",
            "picture": ""
        }
    
    session["user"] = {
        "name": user_info.get("name", "User"),
        "email": user_info.get("email", "user@example.com"),
        "picture": user_info.get("picture", ""),
    }
    
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ========================
# تشغيل التطبيق
# ========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)