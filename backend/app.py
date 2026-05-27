import sys, os
import importlib

sys.path.insert(0, os.path.dirname(__file__))

create_app = importlib.import_module("app.__init__").create_app
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
