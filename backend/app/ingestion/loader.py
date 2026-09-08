
from bs4 import BeautifulSoup
import os
from app.config import DOCUMENTS_DIR
from pathlib import Path


folder_path = DOCUMENTS_DIR
extension = ".html"

def loadDocument()->list[dict]:
    
    output = []
    with os.scandir(folder_path) as entries:
        
        for entry in entries:
            if entry.is_file() and entry.name.endswith(extension):
                #print(f"Found: {entry.name}")
                html = Path(entry.path).read_text(encoding="utf-8")
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()

                main = (soup.find("main")
                    or soup.find("article")
                    or soup.find(id="content")
                    or soup.body
                    or soup)
                text = main.get_text(separator = "\n")
                final_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
                output.append({"doc_id": entry.name.removesuffix(extension), "text": final_text})
            
    return output
        



if __name__ == "__main__":
    output = loadDocument()
    for d in output:
        print(d["doc_id"])