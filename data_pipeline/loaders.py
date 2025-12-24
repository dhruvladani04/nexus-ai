from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_loaders.youtube import YoutubeLoader

class DocumentLoader:
    """Base interface for loading documents."""
    def load(self, source: str) -> List[Document]:
        raise NotImplementedError

class PDFFileLoader(DocumentLoader):
    def load(self, source: str) -> List[Document]:
        """Loads a PDF from a file path."""
        loader = PyPDFLoader(source)
        return loader.load()

class YouTubeVideoLoader(DocumentLoader):
    def load(self, source: str) -> List[Document]:
        """Loads a transcript from a YouTube URL."""
        
        # Method 3: yt-dlp (The Heavy Artillery)
        # This is the most robust way to handle YouTube's anti-bot measures
        import yt_dlp
        import os
        
        ydl_opts = {
            'skip_download': True,      # We only want metadata/subs
            'writesubtitles': True,     # Download subtitles
            'writeautomaticsub': True,  # Download auto-generated subs if needed
            'subtitleslangs': ['en'],   # English only
            'outtmpl': '%(id)s',        # Temp filename
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source, download=False)
                video_title = info.get('title', 'Unknown Title')
                video_id = info.get('id')
                
                # Check for subtitles
                subtitles = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                # Prefer manual english subs, then auto english
                url = None
                if 'en' in subtitles:
                    url = subtitles['en'][0]['url'] # Usually VTT or JSON3
                elif 'en' in auto_subs:
                    url = auto_subs['en'][0]['url']
                
                if not url:
                    raise Exception("No English subtitles found (manual or auto-generated).")
                    
                # We have a URL, but it's raw JSON/VTT. 
                # yt-dlp usually downloads it to disk if we let it, but we skipped download.
                # Actually, simply requests fetching that URL is distinct from 'official' API.
                from langchain_community.document_loaders import YoutubeLoader
                # Let's try LangChain again BUT with 'yt_dlp' translation? 
                # No, simpler: Use requests to get the VTT/JSON3 content.
                
                import requests
                sub_resp = requests.get(url)
                sub_resp.raise_for_status()
                
                # It sends back JSON3 usually
                try:
                    data = sub_resp.json()
                    # Parse JSON3 format
                    events = data.get('events', [])
                    full_text = " ".join(["".join([seg['utf8'] for seg in event.get('segs', [])]) for event in events])
                except:
                    # Fallback if VTT text
                    full_text = sub_resp.text 
                
                metadata = {
                     "source": source,
                     "title": video_title,
                     "author": info.get('uploader', 'Unknown')
                }
                return [Document(page_content=full_text, metadata=metadata)]

        except Exception as e:
            raise Exception(f"yt-dlp failed: {e}")

class WebPageLoader(DocumentLoader):
    def load(self, source: str) -> List[Document]:
        """Loads partial text content from a Web URL."""
        loader = WebBaseLoader(source)
        return loader.load()

def get_loader(source_type: str) -> DocumentLoader:
    if source_type == "resume" or source_type == "pdf":
        return PDFFileLoader()
    elif source_type == "video":
        return YouTubeVideoLoader()
    elif source_type == "web":
        return WebPageLoader()
    else:
        raise ValueError(f"Unknown source type: {source_type}")
