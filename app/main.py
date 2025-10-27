from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.openapi.utils import get_openapi

from app.routes.health import router as health_router
from app.routes.items import router as items_router
from app.routes.brand import router as brand_router
from app.routes.category import router as category_router

app = FastAPI(
    title="The Fake Shop Admin API",
    version="1.0.0",
    # dependencies=[Depends()]   # 👈 Global auth
)

# This sets up Bearer Token security
security_scheme = HTTPBearer()

# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#
#     openapi_schema = get_openapi(
#         title=app.title,
#         version=app.version,
#         description="Admin Panel secured with Bearer Auth",
#         routes=app.routes,
#     )
#
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT"
#         }
#     }
#
#     # Apply security to every method of every path
#     for path in openapi_schema["paths"].values():
#         for operation in path.values():
#             if isinstance(operation, dict):
#                 operation["security"] = [{"BearerAuth": []}]
#
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema
#
# # 👇 Attach it to the app
# app.openapi = custom_openapi

app.include_router(health_router)
app.include_router(items_router)
app.include_router(brand_router)
app.include_router(category_router)

