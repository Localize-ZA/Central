from .auth import router as auth_router
from .supplychain import router as supplychain_router
from fastapi import FastAPI
from dotenv import load_dotenv
from Data.gnn import configure_neo4j

def get_app():
    app = FastAPI()
    
    # load environment variables
    load_dotenv()
    
    # Add middleware here if needed
    #
    
    # Database initialization can be done here if needed
    configure_neo4j()
    
    # Include routers
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(supplychain_router, prefix="/supplychain", tags=["supplychain"])
    
    return app   
    
    