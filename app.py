import os
import uvicorn
import gradio as gr
import spaces
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables
Base.metadata.create_all(bind=engine)

# ============================================================
# @spaces.GPU is REQUIRED for ZeroGPU spaces — DO NOT REMOVE
# ============================================================
@spaces.GPU(duration=5)
def health_check(query: str = ""):
    return "✅ LearnLeague API is running!"

# ============================================================
# Gradio UI
# ============================================================
with gr.Blocks(title="LearnLeague API") as demo:
    gr.Markdown("# 🏆 LearnLeague API")
    gr.Markdown("Backend API for LearnLeague. Use `/docs` for full API reference.")
    with gr.Row():
        inp = gr.Textbox(label="Health Check", placeholder="Type anything...")
        out = gr.Textbox(label="Status")
    gr.Button("Check Status").click(fn=health_check, inputs=inp, outputs=out)

demo.queue()

# ============================================================
# Launch Gradio with prevent_thread_lock so we can add routes
# ============================================================
demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True)

# ============================================================
# Add our FastAPI routes onto the running Gradio server
# ============================================================
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

demo.server.app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

demo.server.app.include_router(auth.router)
demo.server.app.include_router(daily.router)
demo.server.app.include_router(social.router)
demo.server.app.include_router(test.router)
demo.server.app.include_router(tasks.router)

@demo.server.app.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Keep process alive
demo.block_thread()
