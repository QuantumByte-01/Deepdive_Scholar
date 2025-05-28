import app 
from app.routes import create_interface

if __name__ == "__main__":
    demo = create_interface()
    # Bind to localhost so browser can reach it
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
