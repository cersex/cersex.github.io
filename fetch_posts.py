import requests
import os
import json

# --- PERUBAHAN DI SINI ---
# Untuk percobaan, Site ID langsung dimasukkan ke dalam variabel.
# Harap diingat, untuk produksi, sangat disarankan menggunakan GitHub Secrets.
SITE_ID = "143986468" # <--- Site ID Anda langsung di sini!
# --- AKHIR PERUBAHAN ---

API_BASE_URL = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_ID}/posts"

def fetch_wordpress_posts(num_posts=5):
    """
    Mengambil postingan terbaru dari WordPress.com API.
    """
    params = {
        'number': num_posts,
        'status': 'publish', # Hanya postingan yang sudah diterbitkan
        'fields': 'ID,title,content,date,slug' # Field yang ingin diambil
    }
    headers = {
        'User-Agent': 'Python WordPress API Fetcher'
    }

    try:
        response = requests.get(API_BASE_URL, params=params, headers=headers)
        response.raise_for_status() # Akan memunculkan HTTPError untuk status kode error

        data = response.json()
        posts = data.get('posts', [])
        
        processed_posts = []
        for post in posts:
            processed_posts.append({
                'id': post['ID'],
                'title': post['title'],
                'slug': post['slug'],
                'date': post['date'],
                'content': post['content'] # Ini masih HTML, idealnya diubah ke Markdown
            })
        
        return processed_posts

    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return None

def save_posts_to_json(posts, filename="posts.json"):
    """
    Menyimpan data postingan ke file JSON.
    """
    if posts:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(posts)} posts to {filename}")
    else:
        print("No posts to save.")

if __name__ == "__main__":
    print(f"Fetching posts from WordPress.com site ID: {SITE_ID}")
    posts = fetch_wordpress_posts(num_posts=10) # Ambil 10 postingan terbaru
    if posts:
        save_posts_to_json(posts)
        
        # Contoh: Simpan setiap postingan sebagai file Markdown terpisah
        # Ini akan lebih berguna jika Anda menggunakan SSG seperti Jekyll/Hugo
        output_dir = "content/posts"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Saving individual markdown files to {output_dir}")
        for post in posts:
            # Anda perlu mengubah HTML content ke Markdown. Gunakan pustaka seperti `html2text`
            # pip install html2text
            # import html2text
            # markdown_content = html2text.html2text(post['content'])
            
            # Untuk demo sederhana, kita hanya akan menyimpan sebagai HTML untuk saat ini
            filename = os.path.join(output_dir, f"{post['slug']}.md")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"title: \"{post['title']}\"\n")
                f.write(f"date: {post['date']}\n")
                f.write(f"slug: {post['slug']}\n")
                f.write(f"---\n\n")
                f.write(post['content']) # Ini masih HTML, idealnya diubah ke Markdown
            print(f"Saved {filename}")
