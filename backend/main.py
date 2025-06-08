from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Post-Trade Compliance Analyzer backend is running"}

@app.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    contents = await file.read()
    decoded = contents.decode("utf-8")
    print("📄 Uploaded file content:\n", decoded[:500])  # just print first 500 chars
    return {"filename": file.filename, "preview": decoded[:200]}
