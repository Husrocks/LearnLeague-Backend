import os
import gradio as gr
import spaces
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables
Base.metadata.create_all(bind=engine)

# ============================================================
# Gradio UI (required for ZeroGPU spaces - must have @spaces.GPU)
# ============================================================
@spaces.GPU(duration=5)
def health_check(query: str = ""):
    return "✅ LearnLeague API is running! Visit /docs for API reference."

with gr.Blocks(title="LearnLeague API") as demo:
    gr.Markdown("# 🏆 LearnLeague Backend API")
    gr.Markdown("FastAPI backend running inside this Space. Access the full API at `/docs`.")
    with gr.Row():
        inp = gr.Textbox(label="Health Check", placeholder="Type anything and click Check")
        out = gr.Textbox(label="Response")
    btn = gr.Button("Check API Status")
    btn.click(fn=health_check, inputs=inp, outputs=out)

# ============================================================
# Mount our FastAPI routers onto Gradio's built-in FastAPI app
# This avoids the gr.mount_gradio_app() conflict with ZeroGPU
# ============================================================
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

demo.app.include_router(auth.router)
demo.app.include_router(daily.router)
demo.app.include_router(social.router)
demo.app.include_router(test.router)
demo.app.include_router(tasks.router)

@demo.app.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}
