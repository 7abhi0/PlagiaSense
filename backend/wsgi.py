import importlib

create_app = importlib.import_module("app.__init__").create_app

app = create_app()
