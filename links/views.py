from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import Link
from .serializers import LinkSerializer
import urllib.request
import re
import html
from urllib.parse import urlparse

User = get_user_model()

def fetch_url_metadata(url):
    """
    Scrapes page title, open graph meta tags, determines content type,
    and estimates reading time for articles. Used as a fallback and for API/Extension additions.
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    link_type = 'general'
    source_name = domain.replace('www.', '')
    title = "Bilinmeyen Başlık"
    video_id = None
    metadata = {}
    
    # Auto-detect type from domain
    if any(x in domain for x in ['youtube.com', 'youtu.be', 'vimeo.com']):
        link_type = 'video'
        source_name = 'YouTube' if 'youtube' in domain or 'youtu.be' in domain else 'Vimeo'
        # Parse YouTube video_id
        yt_match = re.search(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})', url)
        if yt_match:
            video_id = yt_match.group(1)
    elif any(x in domain for x in ['github.com', 'npmjs.com']):
        link_type = 'code'
        if 'github.com' in domain:
            source_name = 'GitHub'
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) >= 2:
                title = f"{path_parts[0]}/{path_parts[1]}"
                metadata['repo_owner'] = path_parts[0]
                metadata['repo_name'] = path_parts[1]
        else:
            source_name = 'NPM'
    elif any(x in domain for x in ['medium.com', 'substack.com', 'dev.to', 'hashnode.dev', 'wikipedia.org']):
        link_type = 'article'
        if 'medium.com' in domain:
            source_name = 'Medium'
        elif 'substack.com' in domain:
            source_name = 'Substack'
        elif 'dev.to' in domain:
            source_name = 'DEV Community'
    
    # Try fetching the HTML to get title/OG metadata
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([\s\S]*?)<\/title>', html_content, re.IGNORECASE)
            if title_match:
                extracted_title = title_match.group(1).strip()
                title = html.unescape(extracted_title)
            
            # Extract og:site_name
            site_name_match = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE) or \
                              re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']', html_content, re.IGNORECASE)
            if site_name_match:
                source_name = html.unescape(site_name_match.group(1).strip())
                
            # Extract description
            desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE) or \
                         re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE) or \
                         re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', html_content, re.IGNORECASE)
            if desc_match:
                metadata['description'] = html.unescape(desc_match.group(1).strip())
                
            # Extract image
            image_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            if image_match:
                metadata['thumbnail_url'] = image_match.group(1).strip()
                
            # Extract video duration if type is video
            if link_type == 'video':
                duration_match = re.search(r'itemprop=["\']duration["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE) or \
                                 re.search(r'content=["\']([^"\']+)["\']\s+itemprop=["\']duration["\']', html_content, re.IGNORECASE)
                if duration_match:
                    iso_dur = duration_match.group(1).strip()
                    hr_match = re.search(r'(\d+)H', iso_dur, re.IGNORECASE)
                    min_match = re.search(r'(\d+)M', iso_dur, re.IGNORECASE)
                    sec_match = re.search(r'(\d+)S', iso_dur, re.IGNORECASE)
                    
                    hours = int(hr_match.group(1)) if hr_match else 0
                    minutes = int(min_match.group(1)) if min_match else 0
                    seconds = int(sec_match.group(1)) if sec_match else 0
                    
                    if hours > 0:
                        metadata['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        metadata['duration'] = f"{minutes}:{seconds:02d}"
                else:
                    len_match = re.search(r'["\']lengthSeconds["\']\s*:\s*["\']?(\d+)["\']?', html_content) or \
                                re.search(r'["\']approxDurationMs["\']\s*:\s*["\']?(\d+)["\']?', html_content)
                    if len_match:
                        try:
                            total_secs = int(len_match.group(1))
                            if total_secs > 100000:
                                total_secs = round(total_secs / 1000)
                            hours = total_secs // 3600
                            minutes = (total_secs % 3600) // 60
                            seconds = total_secs % 60
                            if hours > 0:
                                metadata['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                metadata['duration'] = f"{minutes}:{seconds:02d}"
                        except ValueError:
                            pass

            # Estimate read time if article and type is general/article
            if link_type == 'article' or link_type == 'general':
                og_type_match = re.search(r'<meta[^>]+property=["\']og:type["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
                if og_type_match and og_type_match.group(1).lower() == 'article':
                    link_type = 'article'
                
                # Strip script and style tags
                text_content = re.sub(r'<(script|style)[^>]*>[\s\S]*?<\/\1>', '', html_content)
                # Strip HTML tags
                text_content = re.sub(r'<[^>]*>', ' ', text_content)
                # Count words
                words = len(re.findall(r'\w+', text_content))
                if words > 100:
                    read_time = max(1, round(words / 200)) # 200 WPM
                    metadata['read_time'] = f"{read_time} dk okuma"
    except Exception as e:
        print(f"Scraping failed inside backend: {e}")
        
    return {
        'type': link_type,
        'title': title,
        'source_name': source_name,
        'video_id': video_id,
        'duration': metadata.get('duration', '0:00'),
        'metadata': metadata
    }

class LinkViewSet(viewsets.ModelViewSet):
    serializer_class = LinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Sync offline/local links with the cloud database.
        Request body should contain a list of links.
        """
        links_data = request.data
        if not isinstance(links_data, list):
            return Response(
                {"error": "Dizi formatında veri bekleniyor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        synced_links = []
        user = request.user

        for data in links_data:
            url = data.get('url')
            if not url:
                continue

            video_id = data.get('video_id') or data.get('videoId')
            is_clean = data.get('is_clean') or data.get('is_watched') or False
            link_type = data.get('type', 'general')
            title = data.get('title', 'Unknown Title')
            source_name = data.get('source_name') or data.get('author_name', 'Unknown Source')
            metadata = data.get('metadata') or {}
            
            # Check if link already exists in user's cloud feed by URL
            link, created = Link.objects.get_or_create(
                user=user,
                url=url,
                defaults={
                    'video_id': video_id,
                    'type': link_type,
                    'title': title,
                    'source_name': source_name,
                    'is_clean': is_clean,
                    'liked': data.get('liked', False),
                    'bookmarked': data.get('bookmarked', False),
                    'duration': data.get('duration', '0:00'),
                    'metadata': metadata,
                    'curator': data.get('curator', '@feed_master'),
                    'category': data.get('category', 'Tech')
                }
            )
            # If it already exists, merge active flags
            if not created:
                modified = False
                incoming_clean = data.get('is_clean') or data.get('is_watched')
                if incoming_clean is not None and not link.is_clean and incoming_clean:
                    link.is_clean = True
                    modified = True
                if data.get('liked') is not None and not link.liked and data.get('liked'):
                    link.liked = True
                    modified = True
                if data.get('bookmarked') is not None and not link.bookmarked and data.get('bookmarked'):
                    link.bookmarked = True
                    modified = True
                if modified:
                    link.save()

            synced_links.append(link)

        # Return updated list of user links
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddLinkByKeyView(APIView):
    permission_classes = [AllowAny]  # Key validation is done inside the view

    def post(self, request):
        # Extract API key
        api_key = request.headers.get('X-Api-Key') or request.query_params.get('api_key') or request.data.get('api_key')
        
        # Also check Authorization header in format: "ApiKey <key>"
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('ApiKey '):
            api_key = auth_header.split(' ')[1]

        if not api_key:
            return Response(
                {"error": "API anahtarı bulunamadı (Headers: X-Api-Key veya Authorization: ApiKey <key>)."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            return Response(
                {"error": "Geçersiz API anahtarı."},
                status=status.HTTP_403_FORBIDDEN
            )

        url = request.data.get('url')
        video_id = request.data.get('video_id') or request.data.get('videoId')
        
        if not url and not video_id:
            return Response(
                {"error": "url veya video_id gereklidir."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if video_id and not url:
            url = f"https://www.youtube.com/watch?v={video_id}"

        # Scrape or fetch metadata
        metadata_scraped = fetch_url_metadata(url)
        
        # Get details from request body or fall back to scraped info
        link_type = request.data.get('type') or metadata_scraped.get('type') or 'general'
        title = request.data.get('title') or metadata_scraped.get('title') or 'Unknown Title'
        source_name = request.data.get('source_name') or request.data.get('author_name') or metadata_scraped.get('source_name') or 'Unknown Source'
        duration = request.data.get('duration')
        if not duration or duration == '0:00':
            duration = metadata_scraped.get('duration') or '0:00'
        curator = request.data.get('curator', '@extension')
        category = request.data.get('category', 'Tech')
        
        # Merge metadata
        metadata = metadata_scraped.get('metadata') or {}
        if isinstance(request.data.get('metadata'), dict):
            metadata.update(request.data.get('metadata'))
            
        final_video_id = video_id or metadata_scraped.get('video_id')

        # Check if already exists for this user by URL
        link, created = Link.objects.get_or_create(
            user=user,
            url=url,
            defaults={
                'video_id': final_video_id,
                'type': link_type,
                'title': title,
                'source_name': source_name,
                'is_clean': False,
                'duration': duration,
                'metadata': metadata,
                'curator': curator,
                'category': category
            }
        )

        serializer = LinkSerializer(link)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({
            "message": "Link başarıyla eklendi." if created else "Link zaten listenizde vardı.",
            "link": serializer.data
        }, status=status_code)
