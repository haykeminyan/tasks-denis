pip install -r requirements.txt
python main.py


folder unzipped pdfs with xlsx and pdf files
script entering into a folder and parsing data from pdf and xlsx and returning diff results values if there is alignment with values



2. fedex api
launch server and send request
* uvicorn fedex_api:app --reload 
* curl -X POST http://127.0.0.1:8000/track \
  -H "Content-Type: application/json" \
  -d '{"tracking_id": "12312341231"}'