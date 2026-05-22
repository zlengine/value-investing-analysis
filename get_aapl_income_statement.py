from sec_api import QueryApi

queryApi = QueryApi(api_key="your_api_key")
query = {
    "query": { "query_string": { "query": "ticker:AAPL AND formType:\"10-K\"" } },
    "from": "0",
    "size": "10",
    "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)