from flask import Flask, render_template
from backend.routes import image_routes
import os

app = Flask(__name__,
            static_folder="static",
            template_folder="templates")
app.register_blueprint(image_routes)

@app.route('/')
def home():
    # دیباگ برای بررسی مسیر فایل قالب
    template_path = os.path.join(app.template_folder, 'index.html')
    print(f"🔍 Checking template path: {template_path}")
    try:
        return render_template('index.html')
    except Exception as e:
        return f"❌ Error loading template: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
