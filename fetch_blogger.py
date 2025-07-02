import requests
import os
import re
import json
import random
from html.parser import HTMLParser

# --- Konfigurasi ---
# Ganti ini dengan ID numerik blog WordPress.com Anda
# Misalnya, '143986468'
BLOG_ID = os.environ.get('WORDPRESS_BLOG_ID', '143986468') 

# Base URL API WordPress.com
API_BASE_URL = f"https://public-api.wordpress.com/rest/v1.1/sites/{BLOG_ID}/posts"

DATA_DIR = 'data'
POST_DIR = 'posts'
LABEL_DIR = 'labels' 
POSTS_JSON = os.path.join(DATA_DIR, 'posts.json')
POSTS_PER_PAGE = 10 # Jumlah postingan per halaman index/label

# Buat direktori jika belum ada
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)

# === Utilitas ===
class ImageExtractor(HTMLParser):
    """Mengekstrak URL gambar pertama dari konten HTML."""
    def __init__(self):
        super().__init__()
        self.thumbnail = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.thumbnail:
            for attr in attrs:
                if attr[0] == 'src':
                    self.thumbnail = attr[1]

def extract_thumbnail(post_data):
    """Mencari gambar unggulan atau mengekstrak dari konten."""
    if post_data.get('featured_image'):
        return post_data['featured_image']
    parser = ImageExtractor()
    parser.feed(post_data.get('content', ''))
    return parser.thumbnail or 'https://pelukjanda.github.io/tema/no-thumbnail.jpg'

def strip_html_and_divs(html):
    """Menghapus semua tag HTML dan div, hanya menyisakan teks."""
    return re.sub(r'</?div[^>]*>', '', re.sub('<[^<]+?>', '', html))

def remove_anchor_tags(html_content):
    """Menghapus tag <a> tetapi mempertahankan teks di dalamnya."""
    return re.sub(r'<a[^>]*>(.*?)<\/a>', r'\1', html_content)

def sanitize_filename(title):
    """Membersihkan judul untuk digunakan sebagai nama file."""
    return re.sub(r'\W+', '-', title.lower()).strip('-')

def render_labels(categories_or_tags):
    """Merender tautan untuk kategori atau tag."""
    if not categories_or_tags:
        return ""
    html = ''
    # WordPress.com API mengembalikan categories/tags sebagai dict {slug: {name: "Name", ...}}
    for slug, data in categories_or_tags.items():
        label_name = data.get('name')
        if label_name:
            filename = sanitize_filename(label_name)
            html += f'<span><a href="/labels/{filename}-1.html">{label_name}</a></span> '
    return html

def load_template(path):
    """Memuat konten template dari file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template, **context):
    """Mengganti placeholder di template dengan nilai konteks."""
    for key, value in context.items():
        template = template.replace(f'{{{{ {key} }}}}', str(value))
    return template

def paginate(total_items, per_page):
    """Menghitung total halaman berdasarkan jumlah item dan item per halaman."""
    total_pages = (total_items + per_page - 1) // per_page
    return total_pages

def generate_pagination_links(base_url, current, total):
    """Menghasilkan tautan paginasi (Previous Posts, Load More)."""
    html = '<div class="pagination-container">'
    if current > 1:
        prev_page_suffix = "" if current - 1 == 1 and "index" in base_url else f"-{current - 1}"
        prev_page_full_url = f"/{base_url}{prev_page_suffix}.html"
        html += f'<span class="pagination-link older-posts"><a href="{prev_page_full_url}">Previous Posts</a></span>'

    if current < total:
        next_page_suffix = f"-{current + 1}"
        next_page_full_url = f"/{base_url}{next_page_suffix}.html"
        html += f'<span class="pagination-link load-more"><a href="{next_page_full_url}">Load More</a></span>'

    html += '<span style="clear:both;"></span>'
    html += '</div>'
    return html

# === Ambil semua postingan dari WordPress.com API ===
def fetch_posts():
    """Mengambil semua postingan dari WordPress.com API."""
    all_posts = []
    offset = 0
    per_request_limit = 100 # Maksimal yang bisa diminta per satu API call

    while True:
        params = {
            'number': per_request_limit,
            'offset': offset,
            'status': 'publish', # Hanya postingan yang terpublikasi
            'fields': 'ID,title,content,excerpt,featured_image,categories,tags,URL' # Bidang yang relevan
        }
        res = requests.get(API_BASE_URL, params=params)

        if res.status_code != 200:
            raise Exception(f"Gagal mengambil data dari WordPress.com API: {res.status_code} - {res.text}. "
                            f"Pastikan BLOG_ID Anda benar dan blog Anda dapat diakses secara publik.")
        
        data = res.json()
        posts = data.get("posts", [])
        total_found = data.get('found', 0) # Total post yang ditemukan

        all_posts.extend(posts)

        # Hentikan paginasi jika tidak ada lagi post atau sudah mencapai total
        if len(posts) < per_request_limit or (offset + len(posts)) >= total_found:
            break
        
        offset += len(posts) # Tingkatkan offset untuk permintaan berikutnya

    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    return all_posts

# === Template (Asumsi post_template.html, index_template.html, label_template.html sudah ada) ===
# Pastikan file-file ini ada di direktori yang sama dengan skrip Anda
# Contoh minimal untuk post_template.html:
# <html><head><title>{{ title }}</title></head><body><h1>{{ title }}</h1><div>{{ content }}</div><div>{{ labels }}</div></body></html>
POST_TEMPLATE = load_template("post_template.html")
INDEX_TEMPLATE = load_template("index_template.html")
LABEL_TEMPLATE = load_template("label_template.html")

# === Halaman per postingan ===
def generate_post_page(post, all_posts):
    """Menghasilkan file HTML untuk setiap postingan."""
    filename_without_path = f"{sanitize_filename(post['title'])}.html"
    filepath = os.path.join(POST_DIR, filename_without_path)

    # Logika related posts (masih ada, tapi bisa dihapus untuk kesederhanaan ekstrem)
    eligible_related = [p for p in all_posts if p['ID'] != post['ID'] and p.get('content')]
    num_related_posts = min(5, len(eligible_related))
    related_sample = random.sample(eligible_related, num_related_posts) if num_related_posts > 0 else []

    related_items_html = []
    for p_related in related_sample:
        related_post_absolute_link = f"/posts/{sanitize_filename(p_related['title'])}.html"
        
        thumb = extract_thumbnail(p_related)
        snippet = strip_html_and_divs(p_related.get('content', ''))
        snippet = snippet[:100] + "..." if len(snippet) > 100 else snippet

        first_label_html = ""
        labels_data = p_related.get('categories') or p_related.get('tags')
        if labels_data:
            label_name = list(labels_data.values())[0].get('name')
            if label_name:
                sanitized_label_name = sanitize_filename(label_name)
                first_label_html = f'<span class="category testing"><a href="/labels/{sanitized_label_name}-1.html">{label_name}</a></span>'

        related_items_html.append(f"""
            <div class="post-card">
                <img class="post-image" src="{thumb}" alt="{p_related["title"]}">
                <div class="post-content">
                    <div class="post-meta">
                        {first_label_html}
                    </div>
                    <h2 class="post-title"><a href="{related_post_absolute_link}">{p_related["title"]}</a></h2>
                    <p class="post-author">By Om Sugeng · <a href="{related_post_absolute_link}">Baca Cerita</a></p>
                </div>
            </div>
        """)
    
    related_html = f"""
    <main class="container">
        <div class="post-list">
            {"".join(related_items_html)}
        </div>
    </main>
    """ if related_items_html else "<p>No related posts found.</p>"

    processed_content = remove_anchor_tags(post.get('content', ''))
    
    labels_to_render = post.get('categories') or post.get('tags')

    # Perhatikan: tidak ada lagi custom_head, custom_header, dll.
    html = render_template(POST_TEMPLATE,
        title=post['title'],
        content=processed_content,
        labels=render_labels(labels_to_render),
        related=related_html
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filename_without_path

# === Halaman index beranda ===
def generate_index(posts):
    """Menghasilkan halaman index beranda dengan paginasi."""
    total_pages = paginate(len(posts), POSTS_PER_PAGE)
    for page in range(1, total_pages + 1):
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        items = posts[start:end]

        items_html = ""
        for post in items:
            post_filename = generate_post_page(post, posts)
            post_absolute_link = f"/posts/{post_filename}"
            
            snippet = strip_html_and_divs(post.get('content', ''))[:100]
            thumb = extract_thumbnail(post)

            first_label_html = ""
            labels_data = post.get('categories') or post.get('tags')
            if labels_data:
                label_name = list(labels_data.values())[0].get('name')
                if label_name:
                    sanitized_label_name = sanitize_filename(label_name)
                    first_label_html = f'<span class="category testing"><a href="/labels/{sanitized_label_name}-1.html">{label_name}</a></span>'
            
            items_html += f"""
<main class="container">
    <div class="post-list">
        <div class="post-card">
            <img class="post-image" src="{thumb}" alt="thumbnail">
            <div class="post-content">
                <div class="post-meta">
                    {first_label_html}
                </div>
                <h2 class="post-title"><a href="{post_absolute_link}">{post['title']}</a></h2>
                <p class="post-author">By Om Sugeng · <a href="{post_absolute_link}">Baca Cerita</a></p>
            </div>
        </div>
    </div>
</main>
"""
        pagination = generate_pagination_links("index", page, total_pages)
        # Perhatikan: tidak ada lagi custom_head, custom_header, dll.
        html = render_template(INDEX_TEMPLATE,
            items=items_html,
            pagination=pagination
        )
        output_file = f"index.html" if page == 1 else f"index-{page}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

# === Halaman per label (category/tag) ===
def generate_label_pages(posts):
    """Menghasilkan halaman terpisah untuk setiap kategori/tag."""
    label_map = {}
    for post in posts:
        labels_data = post.get('categories') or post.get('tags')
        if labels_data:
            for slug, data in labels_data.items():
                label_name = data.get('name')
                if label_name:
                    label_map.setdefault(label_name, []).append(post)

    for label_name, label_posts in label_map.items():
        total_pages = paginate(len(label_posts), POSTS_PER_PAGE)
        for page in range(1, total_pages + 1):
            start = (page - 1) * POSTS_PER_PAGE
            end = start + POSTS_PER_PAGE
            items = label_posts[start:end]

            items_html = ""
            for post in items:
                post_filename = generate_post_page(post, posts)
                post_absolute_link = f"/posts/{post_filename}"
                
                snippet = strip_html_and_divs(post.get('content', ''))[:100]
                thumb = extract_thumbnail(post)

                first_label_html = ""
                labels_data = post.get('categories') or post.get('tags')
                if labels_data:
                    current_post_labels = [data.get('name') for slug, data in labels_data.items() if data.get('name') == label_name]
                    if current_post_labels:
                        sanitized_current_label = sanitize_filename(label_name)
                        first_label_html = f'<span class="category testing"><a href="/labels/{sanitized_current_label}-1.html">{label_name}</a></span>'

                items_html += f"""
<main class="container">
    <div class="post-list">
        <div class="post-card">
            <img class="post-image" src="{thumb}" alt="thumbnail">
            <div class="post-content">
                <div class="post-meta">
                    {first_label_html}
                </div>
                <h2 class="post-title"><a href="{post_absolute_link}">{post['title']}</a></h2>
                <p class="post-author">By Om Sugeng · <a href="{post_absolute_link}">Baca Cerita</a></p>
            </div>
        </div>
    </div>
</main>
"""
            sanitized_label_filename = sanitize_filename(label_name)
            pagination = generate_pagination_links(
                f"labels/{sanitized_label_filename}", page, total_pages
            )
            # Perhatikan: tidak ada lagi custom_head, custom_header, dll.
            html = render_template(LABEL_TEMPLATE,
                label=label_name,
                items=items_html,
                pagination=pagination
            )
            output_file = os.path.join(LABEL_DIR, f"{sanitized_label_filename}-{page}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

# === Eksekusi ===
if __name__ == '__main__':
    print("📥 Mengambil artikel dari WordPress.com API...")
    try:
        posts = fetch_posts()
        print(f"✅ Artikel berhasil diambil: {len(posts)}.")
        generate_index(posts)
        generate_label_pages(posts)
        print("✅ Halaman index, label, dan artikel individual selesai dibuat.")
        print("\nSelesai! Periksa folder 'posts', 'labels', dan file 'index.html'.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
