from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from load_data import load_incremental_data
import os
import time
import math
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"This is path",BASE_DIR)
df = load_incremental_data()

@app.get("/search")
def search(q: str = Query("", min_length=0), field: str = Query(...), page: int = Query(1, ge=1)):
    """
    Perform search with abbrs
    q : query
    field : col
    page : pg number
    return : <list> search results and time
    """
    start_time = time.time()

    page_size = 50
    start_idx = (page - 1) * page_size
    end_idx = page * page_size

    # vec search
    if q == "":
        result = df
    else:
        result = df[df[field].astype(str).str.contains(q, case=False, na=False)]
    total_results = len(result)
    total_pages = math.ceil(total_results / page_size)

    result_page = result.iloc[start_idx:end_idx]

    search_time = time.time() - start_time

    return {
        "data": result_page.to_dict(orient="records"),
        "search_time": search_time,
        "page": page,
        "total_results": total_results,
        "total_pages": total_pages
    }

@app.get("/meta")
def get_metadata():
    return {
        "rows": len(df),
        "columns": df.columns.tolist()
    }