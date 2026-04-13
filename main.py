# This is the main entry point for the FastAPI application. This is used to handle rest api calls into the guild manager database. It also includes the code to set up the database connection and the API key verification for security.
from routers import auctions, currency
from fastapi import FastAPI


app = FastAPI()
                   
# This automatically adds all endpoints from those files
app.include_router(currency.router)
app.include_router(auctions.router)

@app.get("/")
def root():
    return {"message": "Guild API is Online"}
