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

# проверка когда есть excel значение но нет pdf
for excel_file, excel_values in excel_data_per_file.items():
    excel_name = os.path.splitext(excel_file)[0]
    matching_pdf_file = next(
        (pdf_file for pdf_file in pdf_data_per_file if os.path.splitext(pdf_file)[0] == excel_name),
        None
    )

    if not matching_pdf_file:
        print(f"Нет подходящего PDF для Excel: {excel_file}")
        continue

    pdf_values = pdf_data_per_file[matching_pdf_file]
    pdf_numbers = {str(p[0]).strip() for p in pdf_values}

    missing_pdf_numbers = []
    for excel_number in excel_values:
        number = str(excel_number[0]).strip()
        if number not in pdf_numbers:
            missing_pdf_numbers.append({
                'Заявка Excel отсутствующая в PDF': number,
                'Excel выручка': excel_number[1],
                'Excel файл': excel_file
            })
            print(f"{number} отсутствует в {matching_pdf_file}")

    if missing_pdf_numbers:
        df = pd.DataFrame(missing_pdf_numbers)
        res_path = os.path.join(output_folder, f"missing_pdf_values_{excel_name}.csv")
        df.to_csv(res_path, index=False)
        print(f"Несовпадения сохранены: {res_path}")
    else:
        print(f"{excel_file}: все заявки найдены в {matching_pdf_file}")

# проверка когда есть pdf значение но нет excel
for pdf_file, pdf_values in pdf_data_per_file.items():
    pdf_name = os.path.splitext(pdf_file)[0]
    matching_excel_file = next(
        (excel_file for excel_file in excel_data_per_file if os.path.splitext(excel_file)[0] == pdf_name),
        None
    )

    if not matching_excel_file:
        print(f"Нет Excel-файла для PDF: {pdf_file}")
        continue

    excel_values = excel_data_per_file[matching_excel_file]
    excel_numbers = {str(e[0]).strip() for e in excel_values}

    missing_excel_numbers = []
    for pdf_number, pdf_amount in pdf_values:
        number = str(pdf_number).strip()
        if number not in excel_numbers:
            missing_excel_numbers.append({
                'Заявка PDF отсутствующая в EXCEL': number,
                'PDF выручка': pdf_amount,
                'PDF файл': pdf_file
            })
            print(f"{number} отсутствует в {matching_excel_file}")

    if missing_excel_numbers:
        df = pd.DataFrame(missing_excel_numbers)
        res_path = os.path.join(output_folder, f"missing_excel_values_{pdf_name}.csv")
        df.to_csv(res_path, index=False)
        print(f"Несовпадения (PDF→Excel) сохранены: {res_path}")
    else:
        print(f"{pdf_file}: все заявки найдены в Excel {matching_excel_file}")
