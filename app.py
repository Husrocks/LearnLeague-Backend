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
# In Gradio 5.x, use App.create_app to get the FastAPI app
# ============================================================
from gradio.routes import App as GradioApp

server_app = GradioApp.create_app(demo, app_kwargs={})

# Add CORS middleware
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
server_app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount our FastAPI routers onto the Gradio app
server_app.include_router(auth.router)
server_app.include_router(daily.router)
server_app.include_router(social.router)
server_app.include_router(test.router)
server_app.include_router(tasks.router)

@server_app.get("/api")
def read_root():
    return {"message": "Welcome to the LearnLeague Backend API"}

# Run the combined app
uvicorn.run(server_app, host="0.0.0.0", port=7860)
