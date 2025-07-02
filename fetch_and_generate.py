import requests
import os
import json
from datetime import datetime
import markdown # Diperlukan untuk mengkonversi Markdown (jika ada) ke HTML

# Install markdown: pip install markdown

# --- Konfigurasi Anda ---
SITE_ID = "143986468" # Ganti dengan Site ID WordPress.com Anda
OUTPUT_DIR = "docs" # Folder tempat file HTML akan disimpan. GitHub Pages sering menggunakan 'docs' atau root.
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts") # Subfolder untuk halaman detail postingan

API_BASE_URL = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts"

# --- Fungsi untuk Mengambil Postingan dari WordPress.com API ---
def fetch_wordpress_posts(num_posts=10):
    params = {
        'number': num_posts,
        'status': 'publish',
        'fields': 'ID,title,content,date,slug,excerpt,featured_image' # Tambahkan excerpt dan featured_image
    }
    headers = {
        'User-Agent': 'Python GitHub Pages Generator'
    }
    try:
        response = requests.get(API_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        posts = data.get('posts', [])
        
        processed_posts = []
        for post in posts:
            # Konten dari WP API seringkali HTML, tapi bisa juga Markdown jika Anda menulisnya begitu.
            # Kita akan berasumsi bisa jadi HTML dan Markdown jika perlu.
            processed_posts.append({
                'id': post['ID'],
                'title': post['title'],
                'slug': post['slug'],
                'date': post['date'],
                'content': post['content'],
                'excerpt': post.get('excerpt', ''),
                'featured_image': post.get('featured_image', None)
            })
        return processed_posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return None

# --- Fungsi untuk Membuat Template HTML ---
def create_html_page(title, body_content, is_index=False, post_list=None):
    # CSS minimal langsung di dalam HTML untuk kesederhanaan
    css = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        header { background-color: #333; color: #fff; padding: 15px 20px; border-radius: 8px 8px 0 0; text-align: center; margin-bottom: 20px; }
        header h1 { margin: 0; }
        header a { color: #fff; text-decoration: none; }
        nav ul { list-style: none; padding: 0; text-align: center; }
        nav ul li { display: inline; margin-right: 20px; }
        nav ul li a { color: #333; text-decoration: none; font-weight: bold; }
        .post-list { list-style: none; padding: 0; }
        .post-list li { margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        .post-list li:last-child { border-bottom: none; }
        .post-title { color: #007bff; text-decoration: none; }
        .post-title:hover { text-decoration: underline; }
        .post-meta { font-size: 0.9em; color: #777; margin-bottom: 10px; display: block; }
        .post-excerpt { margin-top: 10px; color: #555; }
        .read-more { display: inline-block; margin-top: 10px; color: #007bff; text-decoration: none; font-weight: bold; }
        .read-more:hover { text-decoration: underline; }
        footer { text-align: center; margin-top: 40px; font-size: 0.8em; color: #666; padding-top: 20px; border-top: 1px solid #eee; }
        img { max-width: 100%; height: auto; border-radius: 5px; }
    </style>
    """

    nav_links = """
    <nav>
        <ul>
            <li><a href="index.html">Home</a></li>
            </ul>
    </nav>
    """ if is_index else f'<p><a href="../index.html">&larr; Back to Home</a></p>'

    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
    <div class="container">
        <header>
            <h1><a href="index.html">Blog Saya</a></h1>
        </header>
        {nav_links}
        <main>
            {body_content}
        </main>
        <footer>
            <p>&copy; {datetime.now().year} Blog Saya. Dibuat dengan Python & GitHub Actions.</p>
        </footer>
    </div>
</body>
</html>
    """
    return full_html

# --- Fungsi Utama ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(POSTS_DIR, exist_ok=True)

    print(f"Fetching posts from WordPress.com site ID: {SITE_ID}")
    posts = fetch_wordpress_posts(num_posts=10) # Ambil 10 postingan terbaru

    if posts:
        # Generate individual post HTML files
        for post in posts:
            post_title_escaped = post['title'].replace('"', '&quot;')
            post_date_formatted = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
            
            # Konversi konten jika ada bagian Markdown
            # WordPress API content biasanya HTML, tapi ini safeguard
            post_content_html = markdown.markdown(post['content']) 

            post_body = f"""
            <article>
                <h2>{post_title_escaped}</h2>
                <p class="post-meta">Diterbitkan pada {post_date_formatted}</p>
                {post_content_html}
            </article>
            """
            post_html = create_html_page(post_title_escaped, post_body, is_index=False)
            
            post_filename = os.path.join(POSTS_DIR, f"{post['slug']}.html")
            with open(post_filename, 'w', encoding='utf-8') as f:
                f.write(post_html)
            print(f"Generated post page: {post_filename}")

        # Generate index.html
        index_body_content = "<h2>Postingan Terbaru</h2><ul class='post-list'>"
        for post in posts:
            post_date_formatted = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%B %d, %Y')
            excerpt_html = post['excerpt'] if post['excerpt'] else markdown.markdown(post['content'].split('.')[0] + '...') # Ambil kalimat pertama jika tak ada excerpt
            
            index_body_content += f"""
            <li>
                <h3><a class="post-title" href="posts/{post['slug']}.html">{post['title']}</a></h3>
                <span class="post-meta">Diterbitkan pada {post_date_formatted}</span>
                <div class="post-excerpt">{excerpt_html}</div>
                <a href="posts/{post['slug']}.html" class="read-more">Baca Selengkapnya &rarr;</a>
            </li>
            """
        index_body_content += "</ul>"

        index_html = create_html_page("Blog Saya", index_body_content, is_index=True, post_list=posts)
        with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"Generated index.html in {OUTPUT_DIR}")

    else:
        print("No posts found to generate pages.")
        # Buat index.html kosong jika tidak ada postingan
        index_html = create_html_page("Blog Saya", "<p>Tidak ada postingan yang ditemukan.</p>", is_index=True)
        with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html)
