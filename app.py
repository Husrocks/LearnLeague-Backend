import gradio as gr
import spaces
from src.main import app as fastapi_app

# Create a simple Gradio UI to satisfy Hugging Face's requirement
@spaces.GPU
def health_check(name):
    return "LearnLeague API is running successfully! Access the endpoints at /docs"

demo = gr.Interface(
    fn=health_check, 
    inputs="text", 
    outputs="text",
    title="LearnLeague API Status"
)

# Hugging Face's Gradio SDK looks for an 'app' variable. 
# We mount our FastAPI app and the Gradio UI together.
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

