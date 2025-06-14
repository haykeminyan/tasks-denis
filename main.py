import pdfplumber
import re, os
import pandas as pd

folder = 'pdfs'

# let's define regex
number_regex_pdf = r'Riferimenti:\s*([\d,]+)'
total_regex_pdf = r'TOTALE:EUR\s+(\d+,\d+|\d+)'

number_regex_xlsx = r'Заявка:(\d+)'
total_regex_xlsx = r'Выручка:\s*(-?\d+[.,]?\d*)'

pdf_data_per_file = {}

for filename in os.listdir(folder):
    if filename.lower().endswith('.pdf'):
        path = os.path.join(folder, filename)
        pdf_res = []
        with open(path, 'rb') as f:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    number_match = re.findall(number_regex_pdf, text)
                    total_match = re.findall(total_regex_pdf, text)
                    total_match = [float(i.replace(',', '.')) for i in total_match]
                    if number_match and total_match and len(number_match) == len(total_match):
                        pairs = list(zip(number_match, total_match))
                        pdf_res.extend(pairs)
        pdf_data_per_file[filename] = pdf_res

excel_data_per_file = {}

for filename in os.listdir(folder):
    if filename.lower().endswith('.xlsx'):
        path = os.path.join(folder, filename)
        excel_res = []
        try:
            dfs = pd.read_excel(path, sheet_name=None, engine='openpyxl')
        except Exception as e:
            print(f"Ошибка чтения {filename}: {e}")
            continue

        for sheet_name, df in dfs.items():
            for row in df.itertuples(index=False):
                for cell in row:
                    if isinstance(cell, str):
                        number_match = re.search(number_regex_xlsx, cell)
                        total_match = re.search(total_regex_xlsx, cell)
                        if number_match and total_match:
                            excel_res.append([
                                number_match.group(1),
                                float(total_match.group(1).replace(',', '.'))
                            ])
        excel_data_per_file[filename] = excel_res

# Сравнение и сохранение результата пофайлово
output_folder = os.path.join(folder, 'results')
os.makedirs(output_folder, exist_ok=True)

for pdf_file, pdf_values in pdf_data_per_file.items():
    mismatches = []

    for excel_file, excel_values in excel_data_per_file.items():
        for pdf_entry in pdf_values:
            for excel_entry in excel_values:
                if pdf_entry[0] == excel_entry[0] and abs(float(pdf_entry[1])) != abs(float(excel_entry[1])):
                    mismatches.append({
                        'Заявка': pdf_entry[0],
                        'PDF выручка': pdf_entry[1],
                        'Excel выручка': excel_entry[1],
                        'Excel файл': excel_file
                    })

    if mismatches:
        df = pd.DataFrame(mismatches)
        res_path = os.path.join(output_folder, f"diff_{os.path.splitext(pdf_file)[0]}.csv")
        df.to_csv(res_path, index=False)
        print(f"Несовпадения найдены: {pdf_file} → {res_path}")
    else:
        print(f"OK: {pdf_file} — нет несовпадений")
