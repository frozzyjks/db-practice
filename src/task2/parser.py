import requests
import pandas as pd
import numpy as np
import logging

from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session

from src.task2.database import engine
from src.task2.models import Base, SpimexTradingResults


# =========================
# ЛОГГИРОВАНИЕ (вместо print)
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
}


# =========================
# 1. ПОЛУЧЕНИЕ ССЫЛОК
# =========================
def get_bulletin_links(session, start_year=2023):
    """
    ИЗМЕНЕНИЕ:
    session теперь передаётся извне (не создаётся внутри функции)
    """
    base_url = 'https://spimex.com'
    page_url = 'https://spimex.com/markets/oil_products/trades/results/'

    links = []
    page = 1

    while True:
        response = session.get(
            f'{page_url}?page=page-{page}',
            headers=headers,
            verify=False
        )

        soup = BeautifulSoup(response.text, 'html.parser')

        blocks = soup.find_all('div', class_='accordeon-inner__item')
        if not blocks:
            logger.info(f'Страница {page} пустая — останавливаемся')
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
            logger.info(f'Достигли {start_year} года — останавливаемся')
            break

        logger.info(f'Страница {page}: найдено XLS={len(xls_items)}, всего ссылок: {len(links)}')
        page += 1

    logger.info(f'Всего найдено файлов: {len(links)}')
    return links


# =========================
# 2. DOWNLOAD (отдельно)
# =========================
def download_file(session, url):
    """
    ИЗМЕНЕНИЕ:
    вынесено отдельно → это IO-bound задача
    """
    r = session.get(url, headers=headers, verify=False, allow_redirects=True)

    if r.status_code != 200:
        logger.error(f'Ошибка скачивания {url}: статус {r.status_code}')
        return None

    return r.content


# =========================
# 3. PARSE (отдельно)
# =========================
def parse_file(content, bulletin_date):
    """
    ИЗМЕНЕНИЕ:
    парсинг отделён → это CPU-bound задача
    """

    df = pd.read_excel(BytesIO(content), engine='xlrd', header=None)

    # =========================
    # ЗАМЕНА iterrows → numpy
    # =========================
    row_mask = df.astype(str).apply(
        lambda row: row.str.contains('Единица измерения: Метрическая тонна', na=False).any(),
        axis=1
    )

    indices = np.where(row_mask)[0]
    start_row = indices[0] if len(indices) > 0 else None

    if start_row is None:
        logger.warning(f'Таблица не найдена в файле за {bulletin_date}')
        return None

    header_row = start_row + 1
    data_start = start_row + 3

    # =========================
    # Поиск "Итого" (без iterrows)
    # =========================
    sub = df.iloc[data_start:].astype(str)

    end_mask = sub.apply(
        lambda row: row.str.contains('Итого', na=False).any(),
        axis=1
    )

    end_rows = np.where(end_mask)[0]

    end_row = data_start + end_rows[0] if len(end_rows) > 0 else len(df)

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


# =========================
# 4. СОХРАНЕНИЕ В БД
# =========================
def save_to_db(df, bulletin_date):
    session = Session(engine)

    try:
        exists = session.query(SpimexTradingResults).filter_by(
            date=bulletin_date
        ).first()

        if exists:
            logger.info(f'Пропускаем {bulletin_date} — уже есть')
            return

        # =========================
        # МОЖНО оставить iterrows (не критично для БД)
        # =========================
        records = []
        for _, row in df.iterrows():
            product_id = str(row['exchange_product_id']).strip()

            records.append(SpimexTradingResults(
                exchange_product_id=product_id,
                exchange_product_name=str(row['exchange_product_name']).strip(),
                oil_id=product_id[:4],
                delivery_basis_id=product_id[4:7],
                delivery_type_id=product_id[-1],
                delivery_basis_name=str(row['delivery_basis_name']).strip(),
                volume=float(row['volume']),
                total=float(row['total']),
                count=int(row['count']),
                date=bulletin_date,
            ))

        session.bulk_save_objects(records)
        session.commit()

        logger.info(f'Сохранено: {bulletin_date} — {len(records)} записей')

    except Exception as e:
        session.rollback()
        logger.error(f'Ошибка при сохранении {bulletin_date}: {e}')

    finally:
        session.close()


# =========================
# MAIN
# =========================
if __name__ == '__main__':
    Base.metadata.create_all(engine)

    # =========================
    # ЕДИНАЯ SESSION (важно)
    # =========================
    session = requests.Session()

    links = get_bulletin_links(session, start_year=2023)

    for item in links:
        logger.info(f'Обрабатываем: {item["date"]} — {item["url"]}')

        content = download_file(session, item['url'])

        if content:
            df = parse_file(content, item['date'])

            if df is not None and not df.empty:
                save_to_db(df, item['date'])
            else:
                logger.warning(f'Пропускаем {item["date"]} — нет данных')
        else:
            logger.error(f'Пропускаем {item["date"]} — ошибка скачивания')

    # =========================
    # Проверка
    # =========================
    db_session = Session(engine)

    count = db_session.query(SpimexTradingResults).count()
    first = db_session.query(SpimexTradingResults).first()

    logger.info(f'Всего записей в БД: {count}')

    if first:
        logger.info(f'Первая запись: {first.exchange_product_id} — {first.date}')

    db_session.close()