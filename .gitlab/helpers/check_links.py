import mistune
import requests

class LinkExtractor(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__()
        self.links = []

    def link(self, text, **attrs):  # Accepts text + attributes as kwargs
        self.links.append({
            "url": attrs.get('url') or attrs.get('href'),  # Handle both possible keys
            "text": text
        })
        return super().link(text, **attrs)  # Pass through to parent

# Usage
with open("README.md", "r") as f:
    content = f.read()

renderer = LinkExtractor()
markdown = mistune.create_markdown(renderer=renderer)
markdown(content)
broken_links = []

for link in  renderer.links:
  url = link["url"]
  if url.startswith(("http://", "https://")):
    try:
      response = requests.head(url, allow_redirects=True, timeout=10)
      if response.status_code != 200:
        broken_links.append(f"- ❌ {url} (Status: {response.status_code})")
      else:
        print(f"✅ {url} (OK --> {response.status_code})")
    except Exception as e:
      broken_links.append(f"- ❌ {url} (Error: {str(e)})")

if broken_links:
  print("\n🔗 Broken links found:")
  for link in broken_links:
    print(link)
  with open("broken-links.md", "w") as f:
    f.write("# Broken Links Report\n\n")
    f.write("\n".join(broken_links))
else:
  print("\n✅ All links are working!")
  with open("broken-links.md", "w") as f:
    f.write("# All links are working! 🎉")