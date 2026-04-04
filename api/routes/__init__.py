# Routes - Register all route modules with the app
from api import config
from api.routes import health, brain, stats, utility, chat, llm, motor, external, websocket, train

app = config.app

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(brain.router, prefix="/api", tags=["brain"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(utility.router, prefix="/api", tags=["utility"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(llm.router, prefix="/api", tags=["llm"])
app.include_router(motor.router, prefix="/api", tags=["motor"])
app.include_router(external.router, prefix="/api", tags=["external"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])
app.include_router(train.router, prefix="/api", tags=["train"])