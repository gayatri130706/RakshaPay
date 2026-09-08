with open('server.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))'''

replacement = '''    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/dashboard")
    async def serve_dashboard():
        return FileResponse(os.path.join(static_dir, "dashboard.html"))'''

code = code.replace(target, replacement)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("server.py updated")
