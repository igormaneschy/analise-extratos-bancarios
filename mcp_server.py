import sys, json, asyncio, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from code_indexer import index_code, search_code

WATCH_EXTS = (".py", ".js", ".ts", ".rb", ".java")
WATCH_PATH = os.getenv("CODELLM_PROJECT_PATH", ".")

class CodeWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(WATCH_EXTS):
            print(f"[WATCHER] {event.src_path} modificado", file=sys.stderr)
            try:
                index_code(event.src_path)
            except Exception as e:
                print(f"[WATCHER] Falha ao indexar {event.src_path}: {e}", file=sys.stderr)

def start_watcher(path=WATCH_PATH):
    handler = CodeWatcher()
    observer = Observer()
    observer.schedule(handler, path, recursive=True)
    observer.start()
    print(f"[MCP] Monitorando alterações em: {os.path.abspath(path)}", file=sys.stderr)
    return observer

async def handle_message(message):
    try:
        req = json.loads(message)
        method = req.get("method")
        params = req.get("params", {})

        if method == "searchCode":
            results = search_code(params.get("query", ""), params.get("top_k", 3))
            return {"jsonrpc": "2.0", "id": req.get("id"), "result": results}

        elif method == "indexFile":
            ok = index_code(params.get("file"))
            return {"jsonrpc": "2.0", "id": req.get("id"), "result": ok}

        return {"jsonrpc": "2.0", "id": req.get("id"), "error": "Método desconhecido"}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": None, "error": str(e)}

async def mcp_loop():
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        response = await handle_message(line.strip())
        print(json.dumps(response))


if __name__ == "__main__":
    observer = start_watcher()
    try:
        asyncio.run(mcp_loop())
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
