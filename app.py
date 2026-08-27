import os
import uvicorn
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, daily, social, test, tasks

# Initialize database tables
Base.metadata.create_all(bind=engine)

frontend_url = os.environ.get("FRONTEND_URL", "https://learn-league-platform.vercel.app")

# ============================================================
# Simple Gradio UI (no GPU needed — CPU space)
# ============================================================
def health_check(query: str = ""):
    return "✅ LearnLeague API is running!"

with gr.Blocks(title="LearnLeague API") as demo:
    gr.Markdown("# 🏆 LearnLeague API")
    gr.Markdown("Backend REST API. Visit `/docs` for full API reference.")
    inp = gr.Textbox(label="Health Check")
    out = gr.Textbox(label="Status")
    gr.Button("Check Status").click(fn=health_check, inputs=inp, outputs=out)

demo.queue()

# ============================================================
# FastAPI app with all routes
# ============================================================
api = FastAPI(title="LearnLeague API")

api.add_middleware(
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

api.include_router(auth.router)
api.include_router(daily.router)
api.include_router(social.router)
api.include_router(test.router)
api.include_router(tasks.router)

@api.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Mount Gradio into FastAPI and run
app = gr.mount_gradio_app(api, demo, path="/ui")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
