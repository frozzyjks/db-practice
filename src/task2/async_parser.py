import asyncio
import aiohttp
import pandas as pd
import numpy as np
import logging
import time

from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.task2.models import Base, SpimexTradingResults
from src.task2.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionFactory = async_sessionmaker(async_engine, expire_on_commit=False)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
}


async def get_bulletin_links(session: aiohttp.ClientSession, start_year=2023):
    base_url = 'https://spimex.com'
    page_url = 'https://spimex.com/markets/oil_products/trades/results/'

    links = []
    page = 1

    while True:
        try:
            async with session.get(
                f'{page_url}?page=page-{page}',
                headers=headers,
                ssl=False
            ) as response:
                logger.info(f'Страница {page}: статус {response.status}, URL: {response.url}')
                text = await response.text()

        except Exception as e:
            logger.error(f'Ошибка запроса страницы {page}: {e}')
            break

        soup = BeautifulSoup(text, 'html.parser')

        blocks = soup.find_all('div', class_='accordeon-inner__item')
        logger.info(f'Страница {page}: найдено блоков accordeon-inner__item: {len(blocks)}')

        if not blocks:
            logger.info(f'Страница {page} пустая — останавливаемся')
            break

        xls_items = soup.find_all('a', class_='xls')
        logger.info(f'Страница {page}: найдено xls ссылок всего: {len(xls_items)}')

        xls_items = [
            a for a in xls_items
            if 'oil_xls' in a.get('href', '')
        ]
        logger.info(f'Страница {page}: найдено oil_xls ссылок: {len(xls_items)}')

        if xls_items:
            logger.info(f'Первая ссылка на странице: {xls_items[0].get("href")}')

        stop = False
        for item in xls_items:
            href = item.get('href')
            filename = href.split('/')[-1].split('?')[0]
            date_str = filename.replace('oil_xls_', '')[:8]
            bulletin_date = datetime.strptime(date_str, '%Y%m%d').date()

            if bulletin_date.year < start_year:
                stop = True
                break

            links.append({'url': base_url + href, 'date': bulletin_date})

        if stop:
            logger.info(f'Достигли {start_year} года — останавливаемся')
            break

        logger.info(f'Страница {page}: всего ссылок накоплено: {len(links)}')
        page += 1

    logger.info(f'Всего найдено файлов: {len(links)}')
    return links


async def download_file(session: aiohttp.ClientSession, url: str):
    async with session.get(url, headers=headers, ssl=False, allow_redirects=True) as r:
        if r.status != 200:
            logger.error(f'Ошибка скачивания {url}: статус {r.status}')
            return None
        return await r.read()


def parse_file(content: bytes, bulletin_date):
    df = pd.read_excel(BytesIO(content), engine='xlrd', header=None)

    row_mask = df.astype(str).apply(
        lambda row: row.str.contains('Единица измерения: Метрическая тонна', na=False).any(),
        axis=1
    )

    indices = np.where(row_mask)[0]
    start_row = indices[0] if len(indices) > 0 else None

    if start_row is None:
        return None

    data_start = start_row + 3

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
        'exchange_product_id', 'exchange_product_name',
        'delivery_basis_name', 'volume', 'total', 'count'
    ]

    table = table.dropna(subset=['exchange_product_id'])
    table = table[pd.to_numeric(table['count'], errors='coerce') > 0]
    table['date'] = bulletin_date

    return table


async def save_to_db(df, bulletin_date):
    async with AsyncSessionFactory() as session:
        try:
            result = await session.execute(
                select(SpimexTradingResults).filter_by(date=bulletin_date).limit(1)
            )
            exists = result.scalar_one_or_none()

            if exists:
                logger.info(f'Пропускаем {bulletin_date} — уже есть')
                return

            records = []
            for row in df.itertuples(index=False):
                product_id = str(row.exchange_product_id).strip()
                records.append(SpimexTradingResults(
                    exchange_product_id=product_id,
                    exchange_product_name=str(row.exchange_product_name).strip(),
                    oil_id=product_id[:4],
                    delivery_basis_id=product_id[4:7],
                    delivery_type_id=product_id[-1],
                    delivery_basis_name=str(row.delivery_basis_name).strip(),
                    volume=float(row.volume),
                    total=float(row.total),
                    count=int(row.count),
                    date=bulletin_date,
                ))

            session.add_all(records)
            await session.commit()
            logger.info(f'Сохранено: {bulletin_date} — {len(records)} записей')

        except Exception as e:
            await session.rollback()
            logger.error(f'Ошибка при сохранении {bulletin_date}: {e}')


async def process_item(
    http_session: aiohttp.ClientSession,
    executor: ProcessPoolExecutor,
    item: dict,
    semaphore: asyncio.Semaphore
):
    async with semaphore:
        logger.info(f'Обрабатываем: {item["date"]}')

        content = await download_file(http_session, item['url'])
        if not content:
            logger.warning(f'Пропускаем {item["date"]} — ошибка скачивания')
            return

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(executor, parse_file, content, item['date'])

        if df is not None and not df.empty:
            await save_to_db(df, item['date'])
        else:
            logger.warning(f'Пропускаем {item["date"]} — нет данных')


async def main():
    start_time = time.time()

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    semaphore = asyncio.Semaphore(5)

    executor = ProcessPoolExecutor()

    async with aiohttp.ClientSession() as http_session:
        links = await get_bulletin_links(http_session, start_year=2023)

        tasks = [
            process_item(http_session, executor, item, semaphore)
            for item in links
        ]

        await asyncio.gather(*tasks)

    executor.shutdown(wait=True)

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(SpimexTradingResults))
        count = len(result.scalars().all())
        logger.info(f'Всего записей в БД: {count}')

    elapsed = time.time() - start_time
    logger.info(f'Время выполнения: {elapsed:.1f} секунд')


if __name__ == '__main__':
    asyncio.run(main())