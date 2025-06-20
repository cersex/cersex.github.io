import os
import re
import math

CERITA_FOLDER = 'cerita'
CUSTOM_FOLDER = 'custom'
POSTS_PER_PAGE = 10

def read_custom_file(filename):
    path = os.path.join(CUSTOM_FOLDER, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

def extract_metadata(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    h1_match = re.search(r'<h1.*?>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    category_match = re.search(r'<meta\s+name=["\']category["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    date_match = re.search(r'<meta\s+name=["\']date["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    image_match = re.search(r'<img[^>]+src=["\'](.*?)["\']', content, re.IGNORECASE)

    if title_match and title_match.group(1).strip():
        title = title_match.group(1).strip()
    elif h1_match and h1_match.group(1).strip():
        title = h1_match.group(1).strip()
    else:
        print(f"[Peringatan] Tidak ditemukan <title> atau <h1> di: {filepath}")
        title = os.path.basename(filepath)

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

    # Baca file custom
    custom_head = read_custom_file('custom_head.html')
    custom_js_head = read_custom_file('custom_js_head.html')  # Masih dalam <head>
    custom_header = read_custom_file('custom_header.html')
    custom_sidebar = read_custom_file('custom_sidebar.html')
    custom_footer = read_custom_file('custom_footer.html')
    custom_js_footer = read_custom_file('custom_js_footer.html')

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daftar Cerita - Halaman {page_num}</title>
    {custom_head}
    {custom_js_head}
</head>
<body>
    {custom_header}

    <h1>Daftar Cerita - Halaman {page_num}</h1>
    <ul>
        {''.join(list_items)}
    </ul>
    <div style="margin-top:20px;">
        Halaman: {' | '.join(nav_links)}
    </div>

    {custom_sidebar}
    {custom_footer}
    {custom_js_footer}
</body>
</html>
    """

    filename = 'index.html' if page_num == 1 else f'index{page_num}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"{filename} berhasil dibuat.")

def generate_index():
    files = [
        f for f in os.listdir(CERITA_FOLDER)
        if f.endswith('.html') and not f.startswith('index')
    ]

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
