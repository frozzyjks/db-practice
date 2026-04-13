import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session
from database import engine
from models import Base, SpimexTradingResults

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
}


def get_bulletin_links(start_year=2023):
    base_url = 'https://spimex.com'
    page_url = 'https://spimex.com/markets/oil_products/trades/results/'
    links = []
    page = 1

    session = requests.Session()

    while True:
        response = session.get(
            f'{page_url}?page=page-{page}',
            headers=headers,
            verify=False
        )
        soup = BeautifulSoup(response.text, 'html.parser')

        blocks = soup.find_all('div', class_='accordeon-inner__item')
        if not blocks:
            print(f'Страница {page} пустая — останавливаемся')
            break

        xls_items = soup.find_all('a', class_='xls')
        xls_items = [
            a for a in xls_items
            if 'oil_xls' in a.get('href', '')
        ]

        stop = False
        for item in xls_items:
            href = item.get('href')
            filename = href.split('/')[-1].split('?')[0]
            date_str = filename.replace('oil_xls_', '')[:8]
            bulletin_date = datetime.strptime(date_str, '%Y%m%d').date()

            if bulletin_date.year < start_year:
                stop = True
                break

            links.append({
                'url': base_url + href,
                'date': bulletin_date
            })

        if stop:
            print(f'Достигли {start_year} года — останавливаемся')
            break

        print(f'Страница {page}: найдено XLS={len(xls_items)}, всего ссылок: {len(links)}')
        page += 1

    print(f'Всего найдено файлов: {len(links)}')
    return links


def download_and_parse(url, bulletin_date):
    session = requests.Session()
    r = session.get(url, headers=headers, verify=False, allow_redirects=True)

    if r.status_code != 200:
        print(f'Ошибка скачивания {url}: статус {r.status_code}')
        return None

    df = pd.read_excel(BytesIO(r.content), engine='xlrd', header=None)

    start_row = None
    for i, row in df.iterrows():
        if 'Единица измерения: Метрическая тонна' in str(row.values):
            start_row = i
            break

    if start_row is None:
        print(f'Таблица "Метрическая тонна" не найдена в файле за {bulletin_date}')
        return None

    header_row = start_row + 1
    data_start = start_row + 3

    end_row = None
    for i in range(data_start, len(df)):
        if 'Итого' in str(df.iloc[i].values):
            end_row = i
            break

    if end_row is None:
        end_row = len(df)

    table = df.iloc[data_start:end_row].copy()

    table = table.iloc[:, [1, 2, 3, 4, 5, 14]].copy()
    table.columns = [
        'exchange_product_id',
        'exchange_product_name',
        'delivery_basis_name',
        'volume',
        'total',
        'count'
    ]

    table = table.dropna(subset=['exchange_product_id'])
    table = table[pd.to_numeric(table['count'], errors='coerce') > 0]

    table['date'] = bulletin_date

    return table


def save_to_db(df, bulletin_date):
    session = Session(engine)

    try:
        exists = session.query(SpimexTradingResults).filter_by(
            date=bulletin_date
        ).first()

        if exists:
            print(f'⏭️ Пропускаем {bulletin_date} — данные уже есть в БД')
            return

        records = []
        for _, row in df.iterrows():
            product_id = str(row['exchange_product_id']).strip()
            records.append(SpimexTradingResults(
                exchange_product_id   = product_id,
                exchange_product_name = str(row['exchange_product_name']).strip(),
                oil_id                = product_id[:4],
                delivery_basis_id     = product_id[4:7],
                delivery_type_id      = product_id[-1],
                delivery_basis_name   = str(row['delivery_basis_name']).strip(),
                volume                = float(row['volume']),
                total                 = float(row['total']),
                count                 = int(row['count']),
                date                  = bulletin_date,
            ))

        session.bulk_save_objects(records)
        session.commit()
        print(f'✅ Сохранено: {bulletin_date} — {len(records)} записей')

    except Exception as e:
        session.rollback()
        print(f'❌ Ошибка при сохранении {bulletin_date}: {e}')

    finally:
        session.close()


if __name__ == '__main__':
    Base.metadata.create_all(engine)

    links = get_bulletin_links(start_year=2023)

    for item in links:
        print(f'Обрабатываем: {item["date"]} — {item["url"]}')
        df = download_and_parse(item['url'], item['date'])

        if df is not None and not df.empty:
            save_to_db(df, item['date'])
        else:
            print(f'⚠️ Пропускаем {item["date"]} — данные не найдены')

    session = Session(engine)
    count = session.query(SpimexTradingResults).count()
    first = session.query(SpimexTradingResults).first()
    print(f'\nВсего записей в БД: {count}')
    if first:
        print(f'Первая запись: {first.exchange_product_id} — {first.date}')
    session.close()