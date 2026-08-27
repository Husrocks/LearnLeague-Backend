import os
import gradio as gr
import spaces
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables
Base.metadata.create_all(bind=engine)

# ============================================================
# Multiple @spaces.GPU functions — required for ZeroGPU
# ============================================================
@spaces.GPU(duration=10)
def health_check(query: str = ""):
    return "✅ LearnLeague API is running!"

@spaces.GPU(duration=10)
def get_status(x: str = ""):
    return "🟢 All systems operational"

@spaces.GPU(duration=10)
def ping(x: str = ""):
    return "🏓 Pong! API is healthy."

@spaces.GPU(duration=10)
def check_db(x: str = ""):
    return "🗄️ Database connected"

@spaces.GPU(duration=10)
def api_info(x: str = ""):
    return "📡 LearnLeague REST API v1.0"

# ============================================================
# Gradio UI with all GPU functions registered as event handlers
# ============================================================
with gr.Blocks(title="LearnLeague API") as demo:
    gr.Markdown("# 🏆 LearnLeague API")
    gr.Markdown("Backend REST API. Use `/docs` for full reference.")
    with gr.Tab("Health"):
        inp1 = gr.Textbox(label="Query")
        out1 = gr.Textbox(label="Result")
        gr.Button("Check Health").click(fn=health_check, inputs=inp1, outputs=out1)
    with gr.Tab("Status"):
        inp2 = gr.Textbox(label="Query")
        out2 = gr.Textbox(label="Result")
        gr.Button("Get Status").click(fn=get_status, inputs=inp2, outputs=out2)
    with gr.Tab("Ping"):
        inp3 = gr.Textbox(label="Query")
        out3 = gr.Textbox(label="Result")
        gr.Button("Ping").click(fn=ping, inputs=inp3, outputs=out3)
    with gr.Tab("Database"):
        inp4 = gr.Textbox(label="Query")
        out4 = gr.Textbox(label="Result")
        gr.Button("Check DB").click(fn=check_db, inputs=inp4, outputs=out4)
    with gr.Tab("Info"):
        inp5 = gr.Textbox(label="Query")
        out5 = gr.Textbox(label="Result")
        gr.Button("API Info").click(fn=api_info, inputs=inp5, outputs=out5)

demo.queue()

# ============================================================
# Launch with prevent_thread_lock so we can add routes
# In Gradio 5.x, demo.server_app is the FastAPI app
# ============================================================
demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True, ssr_mode=False)

# Access Gradio 5.x FastAPI app via demo.server_app
fastapi_app = demo.server_app

frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(auth.router)
fastapi_app.include_router(daily.router)
fastapi_app.include_router(social.router)
fastapi_app.include_router(test.router)
fastapi_app.include_router(tasks.router)

@fastapi_app.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Keep the process alive
demo.block_thread()
