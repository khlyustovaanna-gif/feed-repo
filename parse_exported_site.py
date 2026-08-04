#!/usr/bin/env python3
"""
Парсер локально экспортированных HTML‑страниц (Tilda или другая статика)
и генератор CSV для конвертации в feed.xml.

Запуск (в папке с распакованным экспортом):
    python3 parse_exported_site.py --input-dir . --base-url https://sto.cross-export.ru

Выход: feed_template.csv (колонки id,title,description,price,url,image,categoryId)

Примечания:
- Парсер эвристический: для корректного извлечения цен/картинок может потребоваться правка под ваш HTML.
- Если хотите, после создания файла я помогу запустить его пошагово.
"""
import os
import re
import csv
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PRICE_RE = re.compile(r"([0-9\s\u00A0]{1,}[,\.]?[0-9]{0,2})\s*(руб\.|руб|₽|RUB)?", re.I)

def find_price_text(soup_text):
    m = PRICE_RE.search(soup_text)
    if m:
        p = m.group(1)
        p = re.sub(r"[\s\u00A0]", '', p)
        p = p.replace(',', '.')
        return p
    return ''

def extract_from_file(path, base_url):
    with open(path, 'rb') as f:
        raw = f.read()
    try:
        doc = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            doc = raw.decode('windows-1251')
        except Exception:
            doc = raw.decode('utf-8', 'ignore')

    soup = BeautifulSoup(doc, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''

    desc_tag = soup.find('meta', attrs={'name': 'description'})
    desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else ''

    og_url = soup.find('meta', property='og:url')
    canonical = soup.find('link', rel='canonical')
    url = ''
    if og_url and og_url.get('content'):
        url = og_url['content'].strip()
    elif canonical and canonical.get('href'):
        url = canonical['href'].strip()
    else:
        filename = os.path.basename(path)
        url = urljoin(base_url, filename)

    og_image = soup.find('meta', property='og:image')
    image = ''
    if og_image and og_image.get('content'):
        image = urljoin(base_url, og_image['content'].strip())
    else:
        img = soup.find('img')
        if img and img.get('src'):
            image = urljoin(base_url, img['src'])

    price = ''
    price_candidates = []
    for tag in soup.find_all(True, class_=re.compile(r'price|cost|цена', re.I)):
        text = tag.get_text(' ', strip=True)
        if text:
            p = find_price_text(text)
            if p:
                price_candidates.append(p)
    if not price_candidates:
        body_text = soup.get_text(' ', strip=True)
        p = find_price_text(body_text)
        if p:
            price_candidates.append(p)

    if price_candidates:
        price = price_candidates[0]

    return {
        'title': title,
        'description': desc,
        'url': url,
        'image': image,
        'price': price,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', '-i', default='export', help='Папка с распакованным экспортом HTML')
    parser.add_argument('--base-url', '-b', default='https://sto.cross-export.ru', help='Базовый публичный URL сайта')
    parser.add_argument('--output', '-o', default='feed_template.csv', help='Выходной CSV')
    args = parser.parse_args()

    rows = []
    file_id = 1
    for root, dirs, files in os.walk(args.input_dir):
        for fn in files:
            if fn.lower().endswith('.html') or fn.lower().endswith('.htm'):
                path = os.path.join(root, fn)
                data = extract_from_file(path, args.base_url)
                # исключаем явно служебные/пустые страницы
                lower_fn = fn.lower()
                if ('404' in lower_fn) or ('spasibo' in lower_fn) or ('thanks' in lower_fn):
                    continue
                if not data['title'] and not data['price']:
                    continue
                id_ = f"p{file_id}"
                rows.append({
                    'id': id_,
                    'title': data['title'] or fn,
                    'description': data['description'],
                    'price': data['price'] or '0',
                    'url': data['url'],
                    'image': data['image'],
                    'categoryId': '1'
                })
                file_id += 1

    if not rows:
        print('No items found. Проверьте input-dir и структуру HTML.')
        return

    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'description', 'price', 'url', 'image', 'categoryId']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f'Wrote {len(rows)} items to {args.output}')


if __name__ == '__main__':
    main()
