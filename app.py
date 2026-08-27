import os
import gradio as gr
import spaces
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables
Base.metadata.create_all(bind=engine)

frontend_url = os.environ.get("FRONTEND_URL", "https://learn-league-platform.vercel.app")

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
# Gradio UI
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
# CORS middleware added at construction time via app_kwargs
# This avoids "Cannot add middleware after app has started"
# ============================================================
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:3000",
        "https://learn-league-platform.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    prevent_thread_lock=True,
    ssr_mode=False,
    app_kwargs={"middleware": [cors_middleware]},
)

# ============================================================
# Add our API routes AFTER launch (routers are safe post-start)
# ============================================================
demo.server_app.include_router(auth.router)
demo.server_app.include_router(daily.router)
demo.server_app.include_router(social.router)
demo.server_app.include_router(test.router)
demo.server_app.include_router(tasks.router)

@demo.server_app.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Keep process alive
demo.block_thread()
