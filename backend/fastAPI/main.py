from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from load_data import load_incremental_data
import os
import time
import math
import pandas as pd
from fastapi.responses import JSONResponse
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"This is path", BASE_DIR)

df = load_incremental_data()

@app.post("/search")
def search(
    filters: List[Dict[str, Any]] = Body(...),
    page: int = Query(1, ge=1),
    sort_by: str = Query("", min_length=0),
    sort_dir: str = Query("asc"),
    amount_filter: str = Query("no_filter")
):
    """
    Performs filtered, page sliced, sort and cleaned result.

    Args:
        filters (List[Dict[str, Any]]): A list of filter conditions, see Angular app.comp.ts addFilter().
        page (int): The page number of search results (from 1).
        sort_by (str): The column name to sort by. If empty, no sorting is applied.
        sort_dir (str): Sorting direction, either 'asc' or 'desc' with ascend and descend.
        amount_filter (str): Optional filter for the 'Total_Amount_INV_FC' field. Options are 'no_filter', 'filter_wrong', or 'filter_ncv' to remove nothing/ probably wrong data/ most wrong data + NCV (some free).

    Returns:
        dict: A dictionary containing paged result data, total result count, total pages, and search time.
    """

    start_time = time.time()
    result = df.copy()

    for f in filters:
        field = f.get("field")
        operator = f.get("operator")
        value = f.get("value")

        if field not in result.columns or value is None:
            continue

        series = result[field].astype(str)

        if operator == "=":
            result = result[series == str(value)]
        elif operator == "!=":
            result = result[series != str(value)]
        elif operator == ">":
            result = result[pd.to_numeric(series, errors="coerce") > float(value)]
        elif operator == "<":
            result = result[pd.to_numeric(series, errors="coerce") < float(value)]
        elif operator == "contains":
            result = result[series.str.contains(str(value), case=False, na=False)]
        elif operator == "startswith":
            result = result[series.str.startswith(str(value), na=False)]
        elif operator == "endswith":
            result = result[series.str.endswith(str(value), na=False)]

    if sort_by and sort_by in result.columns:
        ascending = sort_dir == "asc"
        result = result.sort_values(by=sort_by, ascending=ascending, na_position="last")

    if "Total_Amount_INV_FC" in result.columns:
        if amount_filter == "filter_wrong":
            result = result[pd.to_numeric(result["Total_Amount_INV_FC"], errors="coerce") >= 0.0001]
        elif amount_filter == "filter_ncv":
            result = result[pd.to_numeric(result["Total_Amount_INV_FC"], errors="coerce") >= 1]

    # page handling
    page_size = 50
    total_results = len(result)
    total_pages = math.ceil(total_results / page_size)
    result_page = result.iloc[(page - 1) * page_size: page * page_size]

    search_time = time.time() - start_time

    return {
        "data": result_page.to_dict(orient="records"),
        "search_time": round(search_time, 4),
        "page": page,
        "total_results": total_results,
        "total_pages": total_pages
    }

@app.get("/meta")
def get_metadata():
    """
    Returns metadata about the dataset.

    Returns:
        dict: A dictionary with total number of rows and list of column names to establish web table.
    """
    return {
        "rows": len(df),
        "columns": df.columns.tolist()
    }

@app.post("/aggregate")
def aggregate(
    filters: List[Dict[str, Any]] = Body(...),
    x_field: str = Query(...),
    y_field: str = Query(...),
    agg: str = Query("sum")
):
    """
    Applies filters and computes an aggregation over the dataset. Like tidyverse in R? "%>%"

    Args:
        filters (List[Dict[str, Any]]): A list of filter conditions, each with 'field', 'operator', and 'value'.
        x_field (str): The column to group by.
        y_field (str): The numeric column to aggregate.
        agg (str): Aggregation type: 'sum', 'avg', or 'count'.

    Returns:
        dict: A dictionary of aggregated values by group. Returns top 20 groups sorted by value.
    """

    result = df.copy()
    for f in filters:
        field = f.get("field")
        op = f.get("operator")
        val = f.get("value")

        if field not in result.columns or val is None:
            continue

        s = result[field].astype(str)
        if op == "=":
            result = result[s == str(val)]
        elif op == "!=":
            result = result[s != str(val)]
        elif op == ">":
            result = result[pd.to_numeric(s, errors="coerce") > float(val)]
        elif op == "<":
            result = result[pd.to_numeric(s, errors="coerce") < float(val)]
        elif op == "contains":
            result = result[s.str.contains(str(val), case=False, na=False)]
        elif op == "startswith":
            result = result[s.str.startswith(str(val), na=False)]
        elif op == "endswith":
            result = result[s.str.endswith(str(val), na=False)]

    if x_field not in result.columns or y_field not in result.columns:
        return {}

    result[y_field] = pd.to_numeric(result[y_field], errors="coerce")

    if agg == "sum":
        grouped = result.groupby(x_field)[y_field].sum()
    elif agg == "avg":
        grouped = result.groupby(x_field)[y_field].mean()
    elif agg == "count":
        grouped = result.groupby(x_field)[y_field].count()
    else:
        return {"error": "Invalid aggregation type."}

    top_grouped = grouped.sort_values(ascending=False).head(20)

    return top_grouped.to_dict()

@app.post("/reload")
def reload_data():
    """
    Manually triggers the load_incremental_data() function

    Returns:
        JSONResponse: Contains the number of total rows after update.
    """

    df = load_incremental_data()
    return JSONResponse({
        "message": "Data reloaded successfully.",
        "total_rows": len(df)
    })