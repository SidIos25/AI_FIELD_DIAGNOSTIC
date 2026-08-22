from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from pathlib import Path
from api.routes import router

app = FastAPI(
    title="AI Field Diagnostic",
    version="0.1.0-beta",
    description="Multi-agent AI system for equipment diagnostics and repair planning",
    contact={
        "name": "Support",
        "email": "sidh@fielddiag.ai"
    },
    docs_url=None,  # Disable default docs to use custom
    redoc_url=None
)

# Serve static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the main UI."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"service": "Field Diagnostic ADK System", "docs": "/docs"}


@app.get("/api-reference", include_in_schema=False)
async def custom_swagger_ui_html():
    """Clean API reference with minimal styling."""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Reference - {app.title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&family=Space+Grotesk:wght@600&display=swap" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css" />
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Poppins', sans-serif;
                background: #0f1419;
                margin: 0;
            }}
            
            .topbar {{ display: none; }}
            
            .nav {{
                background: linear-gradient(90deg, rgba(255,107,91,0.95), rgba(75,184,217,0.95));
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .nav h1 {{
                font-family: 'Space Grotesk', sans-serif;
                color: white;
                font-size: 1.5rem;
                font-weight: 600;
            }}
            
            .back-btn {{
                background: white;
                color: #FF6B5B;
                border: none;
                padding: 10px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.2s;
            }}
            
            .back-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }}
            
            .container {{
                max-width: 1400px;
                margin: 2rem auto;
                padding: 0 2rem;
            }}
            
            #swagger-ui {{
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            }}
            
            #swagger-ui .info .title {{
                font-family: 'Space Grotesk', sans-serif;
            }}
            
            #swagger-ui .btn.execute {{
                background: #FF6B5B;
                border-color: #FF6B5B;
            }}
            
            #swagger-ui .btn.execute:hover {{
                background: #E54D3E;
                border-color: #E54D3E;
            }}
            
            @media (max-width: 768px) {{
                .nav {{ padding: 1rem; }}
                .nav h1 {{ font-size: 1.2rem; }}
                .container {{ padding: 0 1rem; margin: 1rem auto; }}
                #swagger-ui {{ padding: 1.5rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="nav">
            <h1>API Reference</h1>
            <a href="/" class="back-btn">← Home</a>
        </div>
        <div class="container">
            <div id="swagger-ui"></div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                layout: "BaseLayout"
            }});
        </script>
    </body>
    </html>
    """)


app.include_router(router)
