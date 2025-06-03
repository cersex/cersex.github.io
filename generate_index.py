import os
import re
import math

CERITA_FOLDER = 'cerita'
POSTS_PER_PAGE = 10

def extract_metadata(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    category_match = re.search(r'<meta\s+name=["\']category["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    date_match = re.search(r'<meta\s+name=["\']date["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    image_match = re.search(r'<img[^>]+src=["\'](.*?)["\']', content, re.IGNORECASE)

    title = title_match.group(1).strip() if title_match else os.path.basename(filepath)
    category = category_match.group(1).strip() if category_match else "umum"
    date = date_match.group(1).strip() if date_match else "0000-00-00"
    thumbnail = image_match.group(1).strip() if image_match else ""

    return {
        'filename': os.path.basename(filepath),
        'title': title,
        'category': category,
        'date': date,
        'thumbnail': thumbnail
    }

def generate_page(metadata_list, page_num, total_pages):
    list_items = []
    for data in metadata_list:
        link = f"{CERITA_FOLDER}/{data['filename']}"
        thumb_html = f"<img src='{data['thumbnail']}' alt='Thumbnail' style='max-width:120px;margin-right:10px;float:left'>" if data['thumbnail'] else ""
        item = f"""
<li style="overflow:auto;margin-bottom:20px;">
  <a href="{link}">
    {thumb_html}
    <strong>{data['title']}</strong>
  </a><br>
  <em>{data['date']}</em> — [Kategori: {data['category']}]
</li>
"""
        list_items.append(item)

    # Navigasi halaman
    nav_links = []
    for i in range(1, total_pages + 1):
        if i == page_num:
            nav_links.append(f"<strong>{i}</strong>")
        else:
            page_file = 'index.html' if i == 1 else f'index{i}.html'
            nav_links.append(f'<a href="{page_file}">{i}</a>')

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daftar Cerita - Halaman {page_num}</title>
</head>
<body>
    <h1>Daftar Cerita - Halaman {page_num}</h1>
    <ul>
        {''.join(list_items)}
    </ul>
    <div style="margin-top:20px;">
        Halaman: {' | '.join(nav_links)}
    </div>
</body>
</html>
    """

    filename = 'index.html' if page_num == 1 else f'index{page_num}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"{filename} berhasil dibuat.")

def generate_index():
    files = [f for f in os.listdir(CERITA_FOLDER) if f.endswith('.html')]

    metadata_list = []
    for filename in files:
        filepath = os.path.join(CERITA_FOLDER, filename)
        meta = extract_metadata(filepath)
        metadata_list.append(meta)

    # Urutkan berdasarkan tanggal terbaru
    metadata_list.sort(key=lambda x: x['date'], reverse=True)

    total_posts = len(metadata_list)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        page_posts = metadata_list[start:end]
        generate_page(page_posts, page_num, total_pages)

if __name__ == '__main__':
    generate_index()
