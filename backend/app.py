from flask import Flask, render_template
import os
from routes import image_routes

app = Flask(__name__, 
            template_folder=os.path.join(os.getcwd(), "backend/templates"), 
            static_folder=os.path.join(os.getcwd(), "backend/static"))

app.register_blueprint(image_routes)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

