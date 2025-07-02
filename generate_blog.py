import requests
import os
import json
from datetime import datetime
import markdown # Untuk mengkonversi Markdown jika ada di konten WP

# Pastikan Anda telah menginstal pustaka ini: pip install requests markdown

# --- Konfigurasi Anda ---
SITE_ID = "143986468" # Ganti dengan Site ID WordPress.com Anda
OUTPUT_DIR = "docs" # Folder tempat semua file HTML akan disimpan untuk GitHub Pages
POSTS_SUBDIR = "posts" # Subfolder di dalam OUTPUT_DIR untuk halaman detail postingan

API_BASE_URL = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts"

# --- Template HTML Dasar ---
# Ini adalah string multiline untuk struktur dasar setiap halaman HTML
# CSS inline untuk kesederhanaan
BASE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; color: #333; }}
        .container {{ max-width: 800px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        header {{ background-color: #333; color: #fff; padding: 15px 20px; border-radius: 8px 8px 0 0; text-align: center; margin-bottom: 20px; }}
        header h1 {{ margin: 0; }}
        header a {{ color: #fff; text-decoration: none; }}
        nav ul {{ list-style: none; padding: 0; text-align: center; }}
        nav ul li {{ display: inline; margin: 0 10px; }}
        nav ul li a {{ color: #fff; text-decoration: none; font-weight: bold; }}
        .post-list {{ list-style: none; padding: 0; }}
        .post-item {{ margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        .post-item:last-child {{ border-bottom: none; }}
        .post-title {{ color: #007bff; text-decoration: none; }}
        .post-title:hover {{ text-decoration: underline; }}
        .post-meta {{ font-size: 0.9em; color: #777; margin-bottom: 10px; display: block; }}
        .post-excerpt {{ margin-top: 10px; color: #555; }}
        .read-more {{ display: inline-block; margin-top: 10px; color: #007bff; text-decoration: none; font-weight: bold; }}
        .read-more:hover {{ text-decoration: underline; }}
        footer {{ text-align: center; margin-top: 40px; font-size: 0.8em; color: #666; padding-top: 20px; border-top: 1px solid #eee; }}
        img {{ max-width: 100%; height: auto; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><a href="{home_path}">Blog Saya</a></h1>
        </header>
        <main>
            {body_content}
        </main>
        <footer>
            <p>&copy; {current_year} Blog Saya. Dibuat dengan Python & GitHub Actions.</p>
        </footer>
    </div>
</body>
</html>
"""

# --- Fungsi untuk Mengambil Postingan dari WordPress.com API ---
def fetch_wordpress_posts(num_posts=10):
    params = {
        'number': num_posts,
        'status': 'publish',
        'fields': 'ID,title,content,date,slug,excerpt,featured_image'
    }
    headers = {
        'User-Agent': 'Python Static Blog Generator'
    }
    try:
        response = requests.get(API_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        posts = data.get('posts', [])
        
        # Urutkan berdasarkan tanggal terbaru
        posts.sort(key=lambda x: datetime.fromisoformat(x['date'].replace('Z', '+00:00')), reverse=True)
        
        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return None

# --- Fungsi Utama untuk Menghasilkan File HTML ---
if __name__ == "__main__":
    # Buat direktori output utama jika belum ada
    full_output_path = os.path.join(os.getcwd(), OUTPUT_DIR)
    os.makedirs(full_output_path, exist_ok=True)
    
    # Buat subdirektori untuk postingan jika belum ada
    posts_full_path = os.path.join(full_output_path, POSTS_SUBDIR)
    os.makedirs(posts_full_path, exist_ok=True)

    print(f"Fetching posts from WordPress.com site ID: {SITE_ID}")
    posts = fetch_wordpress_posts(num_posts=15) # Ambil 15 postingan terbaru

    if posts:
        # --- 1. Hasilkan halaman detail untuk setiap postingan ---
        print("\nGenerating individual post pages...")
        for post in posts:
            post_title_escaped = post['title'].replace('"', '&quot;')
            post_date_formatted = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
            
            # Konten dari WP API biasanya HTML. Biarkan apa adanya.
            # Jika ada kemungkinan Markdown, Anda bisa menggunakan: markdown.markdown(post['content'])
            post_content_html = post['content'] 

            # Konten halaman detail artikel
            post_body_content = f"""
            <article>
                <h2>{post_title_escaped}</h2>
                <p class="post-meta">Diterbitkan pada {post_date_formatted}</p>
                {post_content_html}
                <p><a href="../index.html">← Kembali ke Halaman Utama</a></p>
            </article>
            """
            
            # Format HTML penuh untuk halaman detail
            full_html = BASE_HTML_TEMPLATE.format(
                title=post_title_escaped,
                home_path="../index.html", # Path ke index.html dari dalam folder posts
                body_content=post_body_content,
                current_year=datetime.now().year
            )
            
            # Tentukan nama file HTML untuk postingan
            post_filename = os.path.join(posts_full_path, f"{post['slug']}.html")
            with open(post_filename, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"  - Generated: {post_filename}")

        # --- 2. Hasilkan halaman index.html (daftar postingan) ---
        print("\nGenerating index.html...")
        index_body_content = "<h2>Postingan Terbaru</h2><ul class='post-list'>"
        for post in posts:
            post_date_formatted = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
            
            # Gunakan excerpt jika tersedia, jika tidak, potong konten dan bersihkan HTML
            snippet = post['excerpt'] if post['excerpt'] else (post['content'].split('.')[0] + '...')
            snippet_clean = snippet.replace('<p>', '').replace('</p>', '').strip() # Bersihkan tag p jika ada
            
            # Tautan ke halaman detail postingan
            article_url = f"{POSTS_SUBDIR}/{post['slug']}.html"

            index_body_content += f"""
            <li class="post-item">
                <h3><a class="post-title" href="{article_url}">{post['title']}</a></h3>
                <span class="post-meta">Diterbitkan pada {post_date_formatted}</span>
                <div class="post-excerpt">{snippet_clean}</div>
                <a href="{article_url}" class="read-more">Baca Selengkapnya &rarr;</a>
            </li>
            """
        index_body_content += "</ul>"

        # Format HTML penuh untuk index.html
        full_html_index = BASE_HTML_TEMPLATE.format(
            title="Blog Saya - Halaman Utama",
            home_path="index.html", # Path ke index.html dari root OUTPUT_DIR
            body_content=index_body_content,
            current_year=datetime.now().year
        )

        index_filename = os.path.join(full_output_path, "index.html")
        with open(index_filename, 'w', encoding='utf-8') as f:
            f.write(full_html_index)
        print(f"  - Generated: {index_filename}")

    else:
        print("No posts found to generate pages.")
        # Buat index.html kosong jika tidak ada postingan
        empty_index_content = "<p>Tidak ada postingan yang ditemukan.</p>"
        full_html_empty_index = BASE_HTML_TEMPLATE.format(
            title="Blog Saya - Halaman Utama",
            home_path="index.html",
            body_content=empty_index_content,
            current_year=datetime.now().year
        )
        index_filename = os.path.join(full_output_path, "index.html")
        with open(index_filename, 'w', encoding='utf-8') as f:
            f.write(full_html_empty_index)
        print("  - Generated empty index.html")
