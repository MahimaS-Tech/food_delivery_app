from fastapi import APIRouter

from app.api.v1.routes import auth, cart, health, orders, restaurants

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(restaurants.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
