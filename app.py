import os
import gradio as gr
import spaces
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

# ============================================================
# @spaces.GPU is REQUIRED for ZeroGPU spaces
# ============================================================
@spaces.GPU(duration=5)
def health_check(query: str = ""):
    return "✅ LearnLeague API is running!"

# ============================================================
# Gradio UI — queue() is mandatory for ZeroGPU
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
# FastAPI app with all our routes
# ============================================================
api = FastAPI(title="LearnLeague API")

frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
api.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(auth.router)
api.include_router(daily.router)
api.include_router(social.router)
api.include_router(test.router)
api.include_router(tasks.router)

@api.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# ============================================================
# Mount Gradio into FastAPI — compatible with Gradio 5.x
# ============================================================
app = gr.mount_gradio_app(api, demo, path="/ui")
