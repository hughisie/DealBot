require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3002;

app.use(cors());
app.use(express.json());

// Decode HTML entities (e.g. &#8217; -> ', &amp; -> &)
const decodeHtmlEntities = (str) => {
    return str
        .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code, 10)))
        .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'")
        .replace(/&nbsp;/g, ' ');
};

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const extractTextFromHtml = (html = '') => {
    return decodeHtmlEntities(String(html).replace(/<[^>]*>?/gm, ' '))
        .replace(/\s+/g, ' ')
        .trim();
};

const splitSentencesFallback = (text) => {
    const input = String(text || '').trim();
    if (!input) return [];

    const sentences = [];
    let start = 0;

    for (let i = 0; i < input.length; i += 1) {
        const ch = input[i];
        if (!'.!?'.includes(ch)) continue;

        const prev = i > 0 ? input[i - 1] : '';
        const next = i + 1 < input.length ? input[i + 1] : '';

        // Keep decimals together (e.g. "2.3 kg")
        if (ch === '.' && /\d/.test(prev) && /\d/.test(next)) continue;

        let j = i + 1;
        while (j < input.length && /["')\]\s]/.test(input[j])) j += 1;

        const current = input.slice(start, j).trim();
        if (current) {
            sentences.push(current);
            start = j;
        }
    }

    const rest = input.slice(start).trim();
    if (rest) sentences.push(rest);
    return sentences;
};

const splitSentences = (text) => {
    const input = String(text || '').trim();
    if (!input) return [];

    if (typeof Intl !== 'undefined' && typeof Intl.Segmenter === 'function') {
        const segmenter = new Intl.Segmenter('en', { granularity: 'sentence' });
        const parts = Array.from(segmenter.segment(input), (part) => part.segment.trim()).filter(Boolean);
        if (parts.length) return parts;
    }

    return splitSentencesFallback(input);
};

const getSentence = (text, n = 1) => {
    const sentences = splitSentences(text);
    if (!sentences.length) return String(text || '').trim();
    return sentences.slice(0, n).join(' ').trim();
};

const sanitizeFileBase = (value = '') => {
    const normalized = value.normalize('NFKD').replace(/[^\x00-\x7F]/g, '');
    return normalized
        .replace(/[<>:"/\\|?*\x00-\x1F]/g, '')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 120);
};

const resolveFallbackImagePath = (title, imageDirectory) => {
    if (!title || !imageDirectory) return null;
    const base = sanitizeFileBase(title);
    if (!base) return null;
    for (const ext of IMAGE_EXTENSIONS) {
        const candidate = path.join(imageDirectory, `${base}${ext}`);
        if (fs.existsSync(candidate)) return candidate;
    }
    return null;
};

const detectImageMime = (filePath) => {
    const ext = path.extname(filePath).toLowerCase();
    if (ext === '.png') return 'image/png';
    if (ext === '.webp') return 'image/webp';
    return 'image/jpeg';
};

const hasVisualLinkPreview = async (url) => {
    const check = async () => {
        const response = await axios.get(url, {
            timeout: 10000,
            maxRedirects: 5,
            headers: { 'User-Agent': 'DistiBot/1.0' }
        });
        const html = String(response.data || '');
        const hasOgImage = /<meta[^>]+property=["']og:image["'][^>]+content=["'][^"']+/i.test(html);
        const hasTwitterImage = /<meta[^>]+name=["']twitter:image["'][^>]+content=["'][^"']+/i.test(html);
        return hasOgImage || hasTwitterImage;
    };

    try {
        const first = await check();
        if (first) return true;
        // Some pages/edges lag before meta tags are fully available.
        await sleep(8000);
        return await check();
    } catch (err) {
        return false;
    }
};

const buildXText = (post) => {
    const X_LIMIT = 280;
    const sentence = getSentence(post.summary, 1);
    const urlPart = `\n\n${post.url}`;
    const maxText = X_LIMIT - urlPart.length;
    const truncated = sentence.length > maxText ? `${sentence.slice(0, Math.max(0, maxText - 1))}…` : sentence;
    return `${truncated}${urlPart}`;
};

const encodeRfc3986 = (str) => encodeURIComponent(str)
    .replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);

const buildOAuthHeader = ({ method, url, consumerKey, consumerSecret, token, tokenSecret, bodyParams = {} }) => {
    const oauth = {
        oauth_consumer_key: consumerKey,
        oauth_nonce: crypto.randomBytes(16).toString('hex'),
        oauth_signature_method: 'HMAC-SHA1',
        oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
        oauth_token: token,
        oauth_version: '1.0'
    };

    const parsed = new URL(url);
    const queryParams = {};
    parsed.searchParams.forEach((value, key) => {
        queryParams[key] = value;
    });
    const signatureParams = { ...oauth, ...queryParams, ...bodyParams };
    const sortedPairs = Object.keys(signatureParams)
        .sort()
        .map((k) => `${encodeRfc3986(k)}=${encodeRfc3986(signatureParams[k])}`)
        .join('&');

    const baseUrl = `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
    const baseString = [
        method.toUpperCase(),
        encodeRfc3986(baseUrl),
        encodeRfc3986(sortedPairs)
    ].join('&');

    const signingKey = `${encodeRfc3986(consumerSecret)}&${encodeRfc3986(tokenSecret || '')}`;
    const signature = crypto.createHmac('sha1', signingKey).update(baseString).digest('base64');
    oauth.oauth_signature = signature;

    const oauthHeader = Object.keys(oauth)
        .sort()
        .map((k) => `${encodeRfc3986(k)}="${encodeRfc3986(oauth[k])}"`)
        .join(', ');
    return `OAuth ${oauthHeader}`;
};

const uploadImageToWordPress = async ({ wpUrl, wpUser, wpAppPassword, imagePath, title }) => {
    if (!wpUrl || !wpUser || !wpAppPassword || !imagePath) return null;
    try {
        const mediaUrl = `${wpUrl.replace(/\/$/, '')}/wp-json/wp/v2/media`;
        const filename = path.basename(imagePath);
        const imageBuffer = fs.readFileSync(imagePath);
        const auth = Buffer.from(`${wpUser}:${wpAppPassword}`).toString('base64');
        const response = await axios.post(mediaUrl, imageBuffer, {
            headers: {
                Authorization: `Basic ${auth}`,
                'Content-Type': detectImageMime(imagePath),
                'Content-Disposition': `attachment; filename="${filename}"`,
                'Content-Length': imageBuffer.length
            },
            params: { title: title || filename },
            timeout: 20000
        });
        return response.data?.source_url || null;
    } catch (err) {
        console.error('WordPress media upload failed:', err.response?.data || err.message);
        return null;
    }
};

const publishToX = async ({ post, fallbackImagePath, x }) => {
    const {
        apiKey,
        apiSecret,
        accessToken,
        accessSecret
    } = x || {};
    if (!apiKey || !apiSecret || !accessToken || !accessSecret) {
        return { skipped: true, reason: 'Missing X credentials' };
    }

    try {
        let mediaId = null;
        if (fallbackImagePath) {
            const mediaData = fs.readFileSync(fallbackImagePath).toString('base64');
            const uploadUrl = 'https://upload.twitter.com/1.1/media/upload.json';
            const uploadBody = { media_data: mediaData };
            const uploadHeader = buildOAuthHeader({
                method: 'POST',
                url: uploadUrl,
                consumerKey: apiKey,
                consumerSecret: apiSecret,
                token: accessToken,
                tokenSecret: accessSecret,
                bodyParams: uploadBody
            });
            const uploadResp = await axios.post(uploadUrl, new URLSearchParams(uploadBody), {
                headers: {
                    Authorization: uploadHeader,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout: 30000
            });
            mediaId = uploadResp.data?.media_id_string || null;
        }

        const tweetUrl = 'https://api.twitter.com/2/tweets';
        const tweetPayload = { text: buildXText(post) };
        if (mediaId) tweetPayload.media = { media_ids: [mediaId] };
        const tweetHeader = buildOAuthHeader({
            method: 'POST',
            url: tweetUrl,
            consumerKey: apiKey,
            consumerSecret: apiSecret,
            token: accessToken,
            tokenSecret: accessSecret
        });
        const tweetResp = await axios.post(tweetUrl, tweetPayload, {
            headers: {
                Authorization: tweetHeader,
                'Content-Type': 'application/json'
            },
            timeout: 15000
        });
        return { success: true, id: tweetResp.data?.data?.id || null, usedFallbackImage: Boolean(mediaId) };
    } catch (err) {
        return { success: false, error: err.response?.data || err.message };
    }
};

const getRedditAccessToken = async ({ clientId, clientSecret, username, password, userAgent }) => {
    const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
    const params = new URLSearchParams({
        grant_type: 'password',
        username,
        password
    });
    const response = await axios.post('https://www.reddit.com/api/v1/access_token', params, {
        headers: {
            Authorization: `Basic ${auth}`,
            'User-Agent': userAgent || 'DistiBot/1.0'
        },
        timeout: 15000
    });
    return response.data?.access_token;
};

const publishToReddit = async ({ post, reddit, fallbackImageUrl }) => {
    const {
        clientId,
        clientSecret,
        username,
        password,
        subreddit,
        userAgent
    } = reddit || {};
    if (!clientId || !clientSecret || !username || !password || !subreddit) {
        return { skipped: true, reason: 'Missing Reddit credentials' };
    }

    try {
        const token = await getRedditAccessToken({ clientId, clientSecret, username, password, userAgent });
        const submitParams = new URLSearchParams({
            api_type: 'json',
            kind: 'link',
            sr: subreddit,
            title: post.title,
            url: post.url,
            resubmit: 'true'
        });
        const flairId = FLAIR_MAP[post.flair];
        if (flairId) submitParams.set('flair_id', flairId);

        const submitResp = await axios.post('https://oauth.reddit.com/api/submit', submitParams, {
            headers: {
                Authorization: `Bearer ${token}`,
                'User-Agent': userAgent || 'DistiBot/1.0'
            },
            timeout: 15000
        });

        const postData = submitResp.data?.json?.data || {};
        const postName = postData?.name;
        if (fallbackImageUrl && postName) {
            const commentParams = new URLSearchParams({
                api_type: 'json',
                thing_id: postName,
                text: `Fallback image: ${fallbackImageUrl}`
            });
            await axios.post('https://oauth.reddit.com/api/comment', commentParams, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'User-Agent': userAgent || 'DistiBot/1.0'
                },
                timeout: 15000
            });
        }

        return { success: true, id: postName || null, usedFallbackImage: Boolean(fallbackImageUrl) };
    } catch (err) {
        return { success: false, error: err.response?.data || err.message };
    }
};

const publishToFacebook = async ({ post, facebook, fallbackImageUrl }) => {
    const { pageOrGroupId, accessToken } = facebook || {};
    if (!pageOrGroupId || !accessToken) {
        return { skipped: true, reason: 'Missing Facebook credentials' };
    }

    try {
        if (fallbackImageUrl) {
            const photoParams = new URLSearchParams({
                url: fallbackImageUrl,
                caption: `${getSentence(post.summary, 1)}\n\n${post.url}`,
                access_token: accessToken
            });
            const photoResp = await axios.post(`https://graph.facebook.com/v22.0/${pageOrGroupId}/photos`, photoParams, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                timeout: 15000
            });
            return { success: true, id: photoResp.data?.id || null, usedFallbackImage: true };
        }

        const feedParams = new URLSearchParams({
            message: getSentence(post.summary, 1),
            link: post.url,
            access_token: accessToken
        });
        const feedResp = await axios.post(`https://graph.facebook.com/v22.0/${pageOrGroupId}/feed`, feedParams, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            timeout: 15000
        });
        return { success: true, id: feedResp.data?.id || null, usedFallbackImage: false };
    } catch (err) {
        return { success: false, error: err.response?.data || err.message };
    }
};

const publishToWhatsAppTargets = async ({ post, token, targets, fallbackImageUrl }) => {
    if (!token) return { skipped: true, reason: 'Missing WhatsApp token' };
    if (!targets.length) return { skipped: true, reason: 'No WhatsApp targets selected' };

    const summary = String(post.summary || '').trim();
    const body = `${summary || getSentence(post.summary, 1)}\n\n${post.url}`;
    const results = [];
    for (const target of targets) {
        try {
            if (fallbackImageUrl) {
                const response = await axios.post('https://gate.whapi.cloud/messages/image', {
                    to: target.jid,
                    media: fallbackImageUrl,
                    caption: body
                }, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 15000
                });
                results.push({ jid: target.jid, success: true, id: response.data?.id || null, usedFallbackImage: true });
            } else {
                const response = await axios.post('https://gate.whapi.cloud/messages/text', {
                    to: target.jid,
                    body,
                    typing_time: 0
                }, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 15000
                });
                results.push({ jid: target.jid, success: true, id: response.data?.id || null, usedFallbackImage: false });
            }
        } catch (err) {
            results.push({ jid: target.jid, success: false, error: err.response?.data || err.message });
        }
    }
    return { success: results.every(r => r.success), results };
};

// Healthy check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

// WP Fetch Posts
app.get('/api/posts', async (req, res) => {
    const wpUrl = req.query.wpUrl || process.env.WP_URL;
    const wpUser = req.query.wpUser || process.env.WP_USER;
    const wpAppPassword = req.query.wpAppPassword || process.env.WP_APP_PASSWORD;

    if (!wpUrl) {
        return res.status(400).json({ error: 'Missing WP URL' });
    }

    const headers = {};
    if (wpUser && wpAppPassword) {
        headers.Authorization = `Basic ${Buffer.from(`${wpUser}:${wpAppPassword}`).toString('base64')}`;
    }

    const after = req.query.after || null; // ISO datetime string

    try {
        let apiUrl = `${wpUrl}/wp-json/wp/v2/posts?_embed&per_page=50`;
        if (after) apiUrl += `&after=${encodeURIComponent(after)}`;
        const response = await axios.get(apiUrl, {
            headers
        });

        // Extract relevant data: Title, URL, first 2 sentences
        const posts = response.data.map(post => {
            const title = decodeHtmlEntities(post.title.rendered);
            const url = post.link;
            const content = extractTextFromHtml(post.content.rendered);
            const sentences = splitSentences(content);
            const summary = sentences.slice(0, 2).join(' ').trim();

            const featuredImage = post._embedded?.['wp:featuredmedia']?.[0]?.source_url || '';

            return {
                id: post.id,
                title,
                url,
                summary,
                featuredImage,
                date: post.date,
                excerpt: extractTextFromHtml(post.excerpt.rendered)
            };
        });

        res.json(posts);
    } catch (error) {
        console.error('WP Fetch Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch posts from WordPress' });
    }
});

// Resolve manual URLs to full WP post data
app.post('/api/resolve-urls', async (req, res) => {
    const { urls, wpUrl, wpUser, wpAppPassword } = req.body;
    const baseUrl = wpUrl || process.env.WP_URL;
    const user = wpUser || process.env.WP_USER;
    const pass = wpAppPassword || process.env.WP_APP_PASSWORD;

    if (!urls || !urls.length) return res.status(400).json({ error: 'Missing urls' });

    const headers = {};
    if (user && pass) {
        headers.Authorization = `Basic ${Buffer.from(`${user}:${pass}`).toString('base64')}`;
    }

    const mapPost = (post) => {
        const title = decodeHtmlEntities(post.title.rendered);
        const url = post.link;
        const content = extractTextFromHtml(post.content.rendered);
        const sentences = splitSentences(content);
        const summary = sentences.slice(0, 2).join(' ').trim();
        const featuredImage = post._embedded?.['wp:featuredmedia']?.[0]?.source_url || '';
        return {
            id: post.id, title, url, summary, featuredImage, date: post.date,
            excerpt: extractTextFromHtml(post.excerpt.rendered)
        };
    };

    const results = await Promise.all(urls.map(async (url) => {
        try {
            // Extract slug from URL (last non-empty path segment)
            const slug = url.replace(/\/$/, '').split('/').pop();
            const apiUrl = `${baseUrl}/wp-json/wp/v2/posts?_embed&slug=${encodeURIComponent(slug)}`;
            const response = await axios.get(apiUrl, { headers });
            if (response.data && response.data.length > 0) {
                return mapPost(response.data[0]);
            }
            // Fallback: stub with just the URL
            return { id: `manual_${slug}`, title: slug, url, summary: url, featuredImage: '', date: new Date().toISOString(), excerpt: '' };
        } catch (e) {
            const slug = url.replace(/\/$/, '').split('/').pop();
            return { id: `manual_${slug}`, title: slug, url, summary: url, featuredImage: '', date: new Date().toISOString(), excerpt: '' };
        }
    }));

    res.json(results);
});

// WhAPI Send Message
app.post('/api/whatsapp/distribute', async (req, res) => {
    const token = req.body.token || process.env.WHAPI_TOKEN;
    const { to, body } = req.body;

    if (!token || !to || !body) {
        return res.status(400).json({ error: 'Missing WhatsApp credentials or content' });
    }

    try {
        const response = await axios.post('https://gate.whapi.cloud/messages/text', {
            to,
            body,
            typing_time: 0
        }, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        res.json({ success: true, response: response.data });
    } catch (error) {
        console.error('WhAPI Error:', error.response?.data || error.message);
        res.status(500).json({ error: 'Failed to send WhatsApp message' });
    }
});

const FLAIR_MAP = {
    "Accident": "c4ed2abe-0e63-11f1-aa35-2a87f4c2aa59",
    "Business": "1bde7a12-8d86-11f0-9b00-6e6d546bea2c",
    "Catalan / Catalonia": "4553c2f6-ab79-11f0-be62-deb6ebe6ed00",
    "Community": "ab77f80e-a5c0-11f0-afc2-12681f807942",
    "Crime": "6b346572-9303-11f0-83e0-964eb27b2511",
    "Economy & Finance": "3f650bcc-8c96-11f0-aa22-fe02919e0041",
    "Environment": "e9955256-8d85-11f0-8d21-6e6d546bea2c",
    "Food & Drink": "e5ab977a-8eea-11f0-bbe4-42144f814757",
    "Health": "4682a56e-dcf9-11f0-8003-7293d864220d",
    "Housing": "7bc7ef62-9303-11f0-bf86-8a21179ca588",
    "News": "6c9fe0d6-ee85-11ee-b695-2618be2a031b",
    "Politics": "2ff2f096-8fb1-11f0-a2e1-b23a67733cf6",
    "Questions": "7885c442-ee85-11ee-90ee-be35c53cd5d3",
    "Science & Tech": "080924c0-8eed-11f0-9908-ce1b763749c7",
    "Shopping": "505c71bc-93a9-11f0-a6da-5abeeae8f674",
    "Tourism": "f79e0d98-8d85-11f0-bce0-3299bc2f155b",
    "Transport": "170de7ac-8c96-11f0-a9a6-e2d623b823c2",
    "Urban Development": "ddff9334-8d85-11f0-9fd2-3299bc2f155b",
    "Whats On": "ff8c2206-8c95-11f0-ae15-e2d623b823c2",
    "Culture": "6c9fe0d6-ee85-11ee-b695-2618be2a031b", // Fallback to News
    "History": "6c9fe0d6-ee85-11ee-b695-2618be2a031b",
    "Meetups": "ab77f80e-a5c0-11f0-afc2-12681f807942", // Fallback to Community
    "Sport": "6c9fe0d6-ee85-11ee-b695-2618be2a031b"
};

// DeepSeek: generate 1-sentence summaries for posts
app.post('/api/summarize', async (req, res) => {
    const { posts, apiKey } = req.body;
    const key = apiKey || process.env.DEEPSEEK_API_KEY;

    if (!key) {
        return res.status(400).json({ error: 'Missing DeepSeek API key' });
    }
    if (!posts || !posts.length) {
        return res.status(400).json({ error: 'Missing posts' });
    }

    try {
        const flairsList = Object.keys(FLAIR_MAP).filter(f => !["Culture", "History", "Meetups", "Sport"].includes(f));
        const summaries = await Promise.all(posts.map(async (post) => {
            const prompt = `Write exactly one punchy, informative sentence (max 200 characters) summarising this news article for social media. 

Also, select the single most appropriate flair from this list:
- "Accident": Crashes, fires, emergencies.
- "Business": Retail, companies, startups.
- "Catalan / Catalonia": Regional identity, language, Catalan-specific news.
- "Community": Local meetups, neighbourhood initiatives, human interest.
- "Crime": Police reports, arrests, safety incidents.
- "Economy & Finance": Markets, inflation, government spending, jobs.
- "Environment": Climate, parks, pollution, sustainability.
- "Food & Drink": Restaurants, bars, culinary news.
- "Health": Hospitals, diseases, wellness.
- "Housing": Renting, mortgages, housing crisis, squats.
- "News": Generic news that doesn't fit elsewhere (Avoid this if possible).
- "Politics": Laws, elections, city hall, strikes, protests.
- "Questions": Queries for the community.
- "Science & Tech": Research, innovation, digital news.
- "Shopping": New store openings, sales.
- "Tourism": Travel trends, visitor issues.
- "Transport": Metro, buses, cycling, traffic, aviation.
- "Urban Development": Construction, city planning, infrastructure.
- "Whats On": Events, festivals, things to do.

Return result STRICTLY as a JSON object with "summary" (the sentence) and "flair" (the selected flair name exactly as written). Do not include markdown codeblocks.

Title: ${post.title}
Excerpt: ${post.excerpt || ''}
Content: ${post.summary} (Full context for better flair selection)`;

            const response = await axios.post('https://api.deepseek.com/chat/completions', {
                model: 'deepseek-chat',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: 100,
                temperature: 0.7,
            }, {
                headers: {
                    'Authorization': `Bearer ${key}`,
                    'Content-Type': 'application/json',
                }
            });

            let parsed = { summary: "", flair: "News" };
            try {
                let content = response.data.choices[0].message.content.trim();
                if (content.startsWith('```json')) {
                    content = content.replace(/^```json\n/, '').replace(/\n```$/, '');
                }
                parsed = JSON.parse(content);
            } catch (e) {
                console.error("Failed to parse DeepSeek response", e);
                parsed.summary = response.data.choices[0].message.content.trim();
            }
            return { id: post.id, summary: parsed.summary, flair: parsed.flair || 'News' };
        }));

        res.json({ success: true, summaries });
    } catch (error) {
        console.error('DeepSeek error:', error.response?.data || error.message);
        res.status(500).json({ error: error.response?.data?.error?.message || error.message });
    }
});

app.post('/api/distribute-direct', async (req, res) => {
    const {
        posts,
        credentials = {},
        jids = [],
        imageDirectory
    } = req.body;

    if (!Array.isArray(posts) || !posts.length) {
        return res.status(400).json({ error: 'Missing posts' });
    }

    const wpConfig = {
        wpUrl: credentials.wpUrl || process.env.WP_URL,
        wpUser: credentials.wpUser || process.env.WP_USER,
        wpAppPassword: credentials.wpAppPassword || process.env.WP_APP_PASSWORD
    };
    const defaultImageDirectory = '/Users/m4owen/Library/CloudStorage/GoogleDrive-gunn0r@gmail.com/Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/10. Post Content/Default';
    const resolvedImageDir = imageDirectory || process.env.DISTIBOT_IMAGE_DIR || defaultImageDirectory;

    const waToken = credentials.whapiToken || process.env.WHAPI_TOKEN;
    const waTargets = (Array.isArray(jids) ? jids : [])
        .filter(j => j && j.jid && j.defaultOn !== false)
        .map(j => ({ jid: j.jid, label: j.label || j.jid }));

    const xConfig = {
        apiKey: credentials.xApiKey || process.env.X_API_KEY,
        apiSecret: credentials.xApiSecret || process.env.X_API_SECRET,
        accessToken: credentials.xAccessToken || process.env.X_ACCESS_TOKEN,
        accessSecret: credentials.xAccessTokenSecret || process.env.X_ACCESS_TOKEN_SECRET
    };
    const redditConfig = {
        clientId: credentials.redditClientId || process.env.REDDIT_CLIENT_ID,
        clientSecret: credentials.redditClientSecret || process.env.REDDIT_CLIENT_SECRET,
        username: credentials.redditUsername || process.env.REDDIT_USERNAME,
        password: credentials.redditPassword || process.env.REDDIT_PASSWORD,
        subreddit: credentials.redditSubreddit || process.env.REDDIT_SUBREDDIT || 'BCNEnglishSpeakers',
        userAgent: credentials.redditUserAgent || process.env.REDDIT_USER_AGENT || 'DistiBot/1.0'
    };
    const facebookConfig = {
        pageOrGroupId: credentials.facebookPageOrGroupId || process.env.FACEBOOK_PAGE_OR_GROUP_ID,
        accessToken: credentials.facebookAccessToken || process.env.FACEBOOK_ACCESS_TOKEN
    };

    try {
        const results = [];
        for (const post of posts) {
            const hasPreview = await hasVisualLinkPreview(post.url);
            const localImagePath = resolveFallbackImagePath(post.title, resolvedImageDir);

            // For X/Facebook, force an attached image when we have a local asset.
            const forcedVisualImagePath = localImagePath || null;
            // For Reddit/WhatsApp, keep fallback behavior when link preview metadata is missing.
            const fallbackImagePath = hasPreview ? null : (localImagePath || null);

            const forcedVisualImageUrl = forcedVisualImagePath
                ? await uploadImageToWordPress({ ...wpConfig, imagePath: forcedVisualImagePath, title: post.title })
                : null;
            const fallbackImageUrl = hasPreview ? null : forcedVisualImageUrl;

            const [xResult, redditResult, waResult, fbResult] = await Promise.all([
                publishToX({ post, fallbackImagePath: forcedVisualImagePath, x: xConfig }),
                publishToReddit({ post, reddit: redditConfig, fallbackImageUrl }),
                publishToWhatsAppTargets({ post, token: waToken, targets: waTargets, fallbackImageUrl }),
                publishToFacebook({ post, facebook: facebookConfig, fallbackImageUrl: forcedVisualImageUrl })
            ]);

            results.push({
                id: post.id,
                title: post.title,
                linkPreviewDetected: hasPreview,
                fallbackImagePath: forcedVisualImagePath || null,
                fallbackImageUrl: forcedVisualImageUrl || null,
                platforms: {
                    x: xResult,
                    reddit: redditResult,
                    whatsapp: waResult,
                    facebook: fbResult
                }
            });
        }

        const platformSuccessCount = results.reduce((acc, postResult) => {
            const platforms = postResult.platforms;
            return acc + ['x', 'reddit', 'whatsapp', 'facebook'].reduce((n, platformKey) => {
                const v = platforms[platformKey];
                return n + (v && v.success ? 1 : 0);
            }, 0);
        }, 0);

        return res.json({
            success: true,
            processedPosts: results.length,
            platformSuccessCount,
            imageDirectoryUsed: resolvedImageDir,
            results
        });
    } catch (err) {
        console.error('Direct distribution error:', err);
        return res.status(500).json({ error: err.message });
    }
});

const ROOT_SOCIAL = '/Users/m4owen/Downloads/01. Social';
const ORDINALS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th'];

function buildAutoPath() {
    const now = new Date();
    const monthNum = String(now.getMonth() + 1).padStart(2, '0');
    const monthName = now.toLocaleString('en-GB', { month: 'long' });
    const day = String(now.getDate()).padStart(2, '0');
    const monthDir = path.join(ROOT_SOCIAL, `${monthNum}. ${monthName}`);
    const dayDir = path.join(monthDir, day);
    // Find next available batch slot
    let batchIdx = 0;
    while (batchIdx < ORDINALS.length) {
        const candidate = path.join(dayDir, `${ORDINALS[batchIdx]} Batch`);
        if (!fs.existsSync(candidate)) return candidate;
        // If it exists but has no HTML files yet, reuse it
        const files = fs.readdirSync(candidate).filter(f => f.endsWith('.html'));
        if (!files.length) return candidate;
        batchIdx++;
    }
    return path.join(dayDir, `${batchIdx + 1}th Batch`);
}

// Return the auto-generated path without creating it
app.get('/api/auto-path', (req, res) => {
    res.json({ path: buildAutoPath() });
});

// Open a folder in Finder
app.post('/api/open-folder', (req, res) => {
    const { folderPath } = req.body;
    if (!folderPath) return res.status(400).json({ error: 'Missing folderPath' });
    const { exec } = require('child_process');
    exec(`open "${folderPath}"`, (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ success: true });
    });
});

// Generate HTML files
app.post('/api/generate-html', (req, res) => {
    const { posts, savePath, whapiToken, jids } = req.body;
    const resolvedWhapiToken = whapiToken || process.env.WHAPI_TOKEN || '';
    const resolvedJids = Array.isArray(jids) && jids.length ? jids : [];

    if (!posts || !posts.length) {
        return res.status(400).json({ error: 'Missing posts' });
    }

    const X_LIMIT = 280;
    const date = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    const count = posts.length;

    const escapeHtml = (value = '') => value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    // X: first sentence + URL, truncated to fit 280 chars
    const buildXText = (post) => {
        const url = post.url;
        const urlPart = `\n\n${url}`;
        const sentence = getSentence(post.summary, 1);
        const maxText = X_LIMIT - urlPart.length;
        const truncated = sentence.length > maxText ? sentence.slice(0, maxText - 1) + '…' : sentence;
        return truncated + urlPart;
    };

    // Reddit: first sentence + URL
    const buildRedditText = (post) => {
        return `${getSentence(post.summary, 1)}\n\n${post.url}`;
    };

    // WhatsApp: full summary + URL
    const buildWhatsAppText = (post) => {
        const summary = String(post.summary || '').trim();
        return `${summary || getSentence(post.summary, 1)}\n\n${post.url}`;
    };

    // --- Reddit HTML ---
    const getRedditUrl = (post) => {
        const title = encodeURIComponent(post.title);
        const body = encodeURIComponent(buildRedditText(post));
        // Keep old.reddit for reliable body prefill; flair must be selected on Reddit page.
        return `https://old.reddit.com/r/BCNEnglishSpeakers/submit?selftext=true&title=${title}&text=${body}`;
    };

    const redditUrls = posts.map(getRedditUrl);

    const redditPostsHtml = posts.map((post, i) => {
        const bodyContent = buildRedditText(post);
        return `
            <div class="post">
                <div class="post-title">${i + 1}. ${post.title}</div>
                <div class="post-preview">
                    <strong>Body text:</strong><br>
                    <div class="body-text" id="body-${i}">${bodyContent.replace(/\n/g, '<br>')}</div>
                    <button class="copy-small" onclick="copyToClipboard('body-${i}')">📋 Copy Body</button>
                </div>
                <div style="margin: 10px 0; font-size: 13px;">
                    <strong>Predicted Flair:</strong> 
                    <span style="background: #eef; color: #44b; padding: 2px 8px; border-radius: 12px; font-weight: bold; border: 1px solid #ccf;">
                        ${escapeHtml(post.flair || 'News')}
                    </span>
                </div>
                <button class="button" onclick="openRedditPost(${i})">
                    🚀 Open Reddit Post ${i + 1}
                </button>
            </div>`;
    }).join('\n');

    const redditHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit Posts - ${count} Articles - ${date}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #ff4500; border-bottom: 3px solid #ff4500; padding-bottom: 15px; margin-bottom: 25px; }
        .post { border: 1px solid #ddd; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; background: white; transition: transform 0.2s, box-shadow 0.2s; }
        .post:hover { transform: translateY(-3px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .post-title { font-weight: bold; font-size: 16px; min-height: 48px; border-bottom: 1px solid #eee; margin-bottom: 12px; padding-bottom: 10px; }
        .post-preview { background: #f9f9f9; padding: 12px; border-radius: 8px; font-size: 12px; color: #555; line-height: 1.4; margin-bottom: 15px; border-left: 3px solid #ff4500; }
        .body-text { margin-top: 5px; color: #333; }
        .copy-small { background: #eee; border: 1px solid #ccc; padding: 2px 6px; font-size: 10px; border-radius: 4px; cursor: pointer; margin-top: 8px; font-weight: bold; }
        .button { background: #ff4500; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; margin-top: auto; }
        .big-button { background: #ff4500; color: white; border: none; padding: 20px 40px; font-size: 20px; border-radius: 30px; cursor: pointer; margin: 30px 0; display: block; width: 100%; font-weight: bold; box-shadow: 0 4px 15px rgba(255,69,0,0.3); }
        .instructions { background: #fff3ef; border-radius: 8px; padding: 20px; border: 1px solid #ffccbc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 Reddit Posts - ${count} Articles</h1>
        <p><strong>Format:</strong> Title + First sentence + URL</p>
        <p><strong>Subreddit:</strong> r/BCNEnglishSpeakers</p>
        <div id="posts">
${redditPostsHtml}
        </div>
        <button class="big-button" onclick="openAllRedditPosts()">
            🚀 OPEN ALL ${count} REDDIT POSTS
        </button>
        <div class="instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li>Click "OPEN ALL" or individual buttons.</li>
                <li><strong>Pop-up Blocker:</strong> If nothing opens, check your browser's address bar to allow pop-ups.</li>
                <li>Verify the <strong>Title</strong> and <strong>Body Text</strong> are correctly filled.</li>
                <li>Select flair on the Old Reddit page before posting.</li>
                <li>If the flair selector does not appear: subreddit mods must enable "Allow submitters to assign their own link flair" in Post Flair settings.</li>
                <li>If the body is empty, manually copy it using the "📋 Copy Body" button.</li>
                <li>Review and click "Post" on each tab.</li>
            </ol>
        </div>
        <script>
            var redditUrls = ${JSON.stringify(redditUrls)};
            function copyToClipboard(elementId) {
                const text = document.getElementById(elementId).innerText;
                navigator.clipboard.writeText(text).then(() => {
                    // Correctly escape the query selector for the client-side script
                    const btn = document.querySelector('[onclick*="' + elementId + '"]');
                    const oldText = btn.innerText;
                    btn.innerText = '✅ Copied!';
                    setTimeout(() => btn.innerText = oldText, 2000);
                });
            }
            function openRedditPost(i) {
                window.open(redditUrls[i], '_blank');
            }
            function openAllRedditPosts() {
                redditUrls.forEach(function(url, i) {
                    setTimeout(function() { window.open(url, '_blank'); }, i * 1000);
                });
            }
        </script>
    </div>
</body>
</html>`;

    // --- Facebook HTML ---
    const FACEBOOK_GROUP_URL = 'https://www.facebook.com/groups/1467537834879289/';
    const buildFacebookText = (post) => `${getSentence(post.summary, 1)}\n\n${post.url}`;
    const fbTexts = posts.map(buildFacebookText);

    const fbPostsHtml = posts.map((post, i) => {
        const fbText = fbTexts[i];
        return `
            <div class="post">
                <div class="post-title">${i + 1}. ${post.title}</div>
                <div class="post-preview">
                    <strong>Post text:</strong><br>
                    <div class="body-text" id="fb-body-${i}">${fbText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')}</div>
                </div>
                <div class="row">
                    <button class="copy-small" onclick="copyToClipboard('fb-body-${i}', this)">📋 Copy Text</button>
                    <button class="button" onclick="openFacebookGroup()">
                        📘 Open Facebook Group
                    </button>
                </div>
            </div>`;
    }).join('\n');

    const facebookHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Posts - ${count} Articles - ${date}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #eef3fb; }
        .container { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1877f2; border-bottom: 3px solid #1877f2; padding-bottom: 15px; margin-bottom: 25px; }
        .post { border: 1px solid #dbe3f1; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; background: white; margin-bottom: 14px; }
        .post-title { font-weight: bold; font-size: 16px; min-height: 48px; border-bottom: 1px solid #eef2f8; margin-bottom: 12px; padding-bottom: 10px; }
        .post-preview { background: #f6f9ff; padding: 12px; border-radius: 8px; font-size: 12px; color: #555; line-height: 1.4; margin-bottom: 12px; border-left: 3px solid #1877f2; }
        .body-text { margin-top: 5px; color: #333; }
        .row { display: flex; gap: 8px; flex-wrap: wrap; }
        .copy-small { background: #eef2f8; border: 1px solid #c7d2e5; padding: 8px 12px; font-size: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .button { background: #1877f2; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .big-button { background: #1877f2; color: white; border: none; padding: 16px 24px; font-size: 18px; border-radius: 28px; cursor: pointer; margin: 20px 0; display: block; width: 100%; font-weight: bold; }
        .instructions { background: #f3f8ff; border-radius: 8px; padding: 20px; border: 1px solid #d6e5ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📘 Facebook Group Posts - ${count} Articles</h1>
        <p><strong>Group:</strong> BCN English Speakers</p>
        <p><strong>Format:</strong> First sentence, blank line, article URL</p>
        <button class="big-button" onclick="openFacebookGroup()">📘 OPEN FACEBOOK GROUP</button>
        <div id="posts">
${fbPostsHtml}
        </div>
        <div class="instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li>Open the group once using the blue button.</li>
                <li>Click "Copy Text" for the post you want to publish.</li>
                <li>Paste into the Facebook group composer and post.</li>
            </ol>
        </div>
        <script>
            var facebookGroupUrl = ${JSON.stringify(FACEBOOK_GROUP_URL)};
            function openFacebookGroup() {
                window.open(facebookGroupUrl, '_blank');
            }
            function copyToClipboard(elementId, btn) {
                const text = document.getElementById(elementId).innerText;
                navigator.clipboard.writeText(text).then(() => {
                    const oldText = btn.innerText;
                    btn.innerText = '✅ Copied!';
                    setTimeout(() => btn.innerText = oldText, 1800);
                });
            }
        </script>
    </div>
</body>
</html>`;

    // --- X HTML ---
    const xUrls = posts.map((post) => {
        const xText = buildXText(post);
        return `https://x.com/intent/post?text=${encodeURIComponent(xText)}`;
    });

    const xPostsHtml = posts.map((post, i) => {
        const xText = buildXText(post);
        const charCount = xText.length;
        return `
            <div class="tweet">
                <div class="tweet-title">${i + 1}. ${post.title}</div>
                <div class="tweet-text">${xText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                <div class="tweet-meta">
                    <div class="tweet-length">${charCount}/280 characters</div>
                    <button class="button" onclick="openXTweet(${i})">
                        Open X/Twitter ${i + 1}
                    </button>
                </div>
            </div>`;
    }).join('\n');

    const xHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X/Twitter Posts - ${count} Articles - ${date}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f8fa; }
        .container { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1DA1F2; border-bottom: 3px solid #1DA1F2; padding-bottom: 15px; margin-bottom: 25px; }
        .tweet { border: 1px solid #e1e8ed; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .tweet-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; }
        .tweet-text { color: #14171a; margin-bottom: 15px; line-height: 1.5; white-space: pre-line; }
        .tweet-length { font-size: 12px; color: #657786; background: #f5f8fa; padding: 4px 8px; border-radius: 4px; }
        .button { background: #1DA1F2; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; }
        .big-button { background: #1DA1F2; color: white; border: none; padding: 20px 40px; font-size: 20px; border-radius: 30px; cursor: pointer; margin: 30px 0; display: block; width: 100%; font-weight: bold; }
        .instructions { background: #e8f4fd; border-radius: 8px; padding: 20px; margin-top: 20px; }
        .tweet-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐦 X/Twitter Posts - ${count} Articles</h1>
        <p><strong>Format:</strong> First sentence + URL (within 280 characters)</p>
        <p><strong>Character limit:</strong> All under 280 characters</p>
        <div id="tweets">
${xPostsHtml}
        </div>
        <button class="big-button" onclick="openAllXTweets()">
            🚀 OPEN ALL ${count} X/TWITTER POSTS
        </button>
        <div class="instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li>Click "OPEN ALL ${count} X/TWITTER POSTS" button</li>
                <li>Allow browser popups when prompted</li>
                <li>Log into X/Twitter if needed</li>
                <li>Review each tweet before posting</li>
                <li>All tweets are within the 280 character limit</li>
            </ol>
        </div>
        <script>
            var xUrls = ${JSON.stringify(xUrls)};
            function openXTweet(i) {
                window.open(xUrls[i], '_blank');
            }
            function openAllXTweets() {
                xUrls.forEach(function(url, i) {
                    setTimeout(function() { window.open(url, '_blank'); }, i * 800);
                });
            }
        </script>
    </div>
</body>
</html>`;

    // --- WhatsApp HTML ---
    const waTexts = posts.map(post => buildWhatsAppText(post));

    const waPostsHtml = posts.map((post, i) => {
        const waText = waTexts[i];
        return `
            <div class="post" id="post-${i}">
                <div class="post-title">${i + 1}. ${post.title}</div>
                <div class="post-text">${waText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')}</div>
                <div class="target-row" id="target-row-${i}"></div>
                <div class="action-row">
                    <button class="button" id="btn-${i}" onclick="copyMessage(${i}, this)">✓ Copy</button>
                    <button class="send-selected-btn" onclick="sendSelected(${i}, this)">📤 Send to Selected</button>
                </div>
                <div class="status-bar" id="status-${i}"></div>
            </div>`;
    }).join('\n');

    const waHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Posts - ${count} Articles - ${date}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f0f2f5; }
        .container { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #25D366; border-bottom: 3px solid #25D366; padding-bottom: 15px; margin-bottom: 25px; }
        .post { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .post-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
        .post-text { color: #333; line-height: 1.5; margin-bottom: 12px; white-space: pre-line; background: #f0f2f5; padding: 10px; border-radius: 6px; }
        .button { background: #25D366; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }
        .button.copied { background: #128C7E; }
        .send-selected-btn { background: #075E54; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s; margin-left: 6px; }
        .send-selected-btn:disabled { background: #aaa; cursor: default; }
        .post.copied { background: #e6f9ee; border-color: #25D366; }
        .post.all-sent { background: #dff5e8; border-color: #25D366; }
        .action-row { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
        .target-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; padding: 8px 10px; background: #f7f7f7; border-radius: 6px; }
        .target-row label { display: flex; align-items: center; gap: 5px; font-size: 13px; cursor: pointer; user-select: none; }
        .target-row input[type=checkbox] { width: 15px; height: 15px; accent-color: #075E54; cursor: pointer; }
        .status-bar { font-size: 12px; color: #555; margin-top: 6px; min-height: 16px; }
        .bulk-section { background: #f0fff4; border: 1px solid #b2dfdb; border-radius: 10px; padding: 16px 20px; margin-bottom: 24px; }
        .bulk-section h3 { color: #075E54; margin: 0 0 10px 0; font-size: 15px; }
        .bulk-row { display: flex; flex-wrap: wrap; gap: 8px; }
        .bulk-btn { background: #075E54; color: white; border: none; padding: 10px 22px; border-radius: 24px; cursor: pointer; font-size: 14px; font-weight: bold; transition: background 0.2s; }
        .bulk-btn:disabled { background: #aaa; cursor: default; }
        .bulk-btn.done { background: #128C7E; }
        .instructions { background: #f0fff4; border-radius: 8px; padding: 20px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 WhatsApp Posts - ${count} Articles</h1>
        <p><strong>Format:</strong> One sentence + URL</p>
        <div id="posts">
${waPostsHtml}
        </div>
        <div id="send-all-container"></div>
        <div class="instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li>Click "Copy Message" for each post</li>
                <li>Paste into WhatsApp group or channel</li>
                <li>Send each message individually</li>
            </ol>
        </div>
        <script>
            var waTexts = ${JSON.stringify(waTexts)};
            var whapiToken = ${JSON.stringify(resolvedWhapiToken)};
            var jids = ${JSON.stringify(resolvedJids)};

            function copyMessage(i, btn) {
                var markCopied = function() {
                    btn.textContent = '\u2713 Copied!';
                    btn.classList.add('copied');
                    btn.closest('.post').classList.add('copied');
                };
                navigator.clipboard.writeText(waTexts[i]).then(markCopied).catch(function() {
                    var ta = document.createElement('textarea');
                    ta.value = waTexts[i];
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    markCopied();
                });
            }

            // Returns array of checked JID objects for a given post index
            function getCheckedJids(postIdx) {
                var row = document.getElementById('target-row-' + postIdx);
                if (!row) return [];
                return Array.from(row.querySelectorAll('input[type=checkbox]'))
                    .filter(function(cb) { return cb.checked; })
                    .map(function(cb) { return JSON.parse(cb.dataset.jid); });
            }

            function sendOneToJid(postIdx, jidObj, statusEl, onDone) {
                return fetch('https://gate.whapi.cloud/messages/text', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + whapiToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ to: jidObj.jid, body: waTexts[postIdx], typing_time: 0 })
                }).then(function(r) {
                    if (!r.ok) return r.text().then(function(t) { throw new Error(t); });
                    if (statusEl) statusEl.textContent += '\u2713 ' + jidObj.label + '  ';
                    // tick the checkbox label green
                    var row = document.getElementById('target-row-' + postIdx);
                    if (row) {
                        row.querySelectorAll('input[type=checkbox]').forEach(function(cb) {
                            if (JSON.parse(cb.dataset.jid).jid === jidObj.jid) {
                                cb.parentElement.style.color = '#128C7E';
                                cb.parentElement.style.fontWeight = 'bold';
                            }
                        });
                    }
                    if (onDone) onDone();
                }).catch(function(e) {
                    if (statusEl) statusEl.textContent += '\u2717 ' + jidObj.label + ': ' + e.message + '  ';
                });
            }

            function sendSelected(postIdx, btn) {
                if (!whapiToken) { alert('No WhAPI token configured.'); return; }
                var targets = getCheckedJids(postIdx);
                if (!targets.length) { alert('No channels selected for this post.'); return; }
                btn.disabled = true;
                btn.textContent = '\u23f3 Sending\u2026';
                var statusEl = document.getElementById('status-' + postIdx);
                if (statusEl) statusEl.textContent = '';
                var chain = Promise.resolve();
                targets.forEach(function(jidObj) {
                    chain = chain.then(function() { return sendOneToJid(postIdx, jidObj, statusEl, null); });
                });
                chain.then(function() {
                    btn.disabled = false;
                    btn.textContent = '\u2713 Sent';
                    document.getElementById('post-' + postIdx).classList.add('all-sent');
                });
            }

            // Bulk: send all posts to a single JID (only posts where that JID is checked)
            function sendAllToJid(jidObj, btn) {
                if (!whapiToken) { alert('No WhAPI token configured.'); return; }
                btn.disabled = true;
                btn.textContent = '\u23f3 Sending\u2026';
                var eligible = [];
                waTexts.forEach(function(_, i) {
                    var checked = getCheckedJids(i);
                    if (checked.some(function(j) { return j.jid === jidObj.jid; })) eligible.push(i);
                });
                var chain = Promise.resolve();
                eligible.forEach(function(postIdx, n) {
                    chain = chain.then(function() {
                        return new Promise(function(resolve) {
                            setTimeout(function() {
                                var statusEl = document.getElementById('status-' + postIdx);
                                sendOneToJid(postIdx, jidObj, statusEl, resolve);
                            }, n === 0 ? 0 : 800);
                        });
                    });
                });
                chain.then(function() {
                    btn.classList.add('done');
                    btn.textContent = '\u2713 Done \u2014 ' + jidObj.label;
                });
            }

            window.addEventListener('DOMContentLoaded', function() {
                if (!jids.length || !whapiToken) return;

                // Build per-post checkbox rows
                waTexts.forEach(function(_, i) {
                    var row = document.getElementById('target-row-' + i);
                    if (!row) return;
                    jids.forEach(function(jidObj) {
                        var label = document.createElement('label');
                        var cb = document.createElement('input');
                        cb.type = 'checkbox';
                        cb.checked = jidObj.defaultOn !== false;
                        cb.dataset.jid = JSON.stringify(jidObj);
                        label.appendChild(cb);
                        label.appendChild(document.createTextNode(' ' + jidObj.label));
                        row.appendChild(label);
                    });
                });

                // Build bulk send buttons
                var container = document.getElementById('send-all-container');
                if (!container) return;
                var section = document.createElement('div');
                section.className = 'bulk-section';
                section.innerHTML = '<h3>\ud83d\ude80 Bulk Send</h3><p style="font-size:12px;color:#555;margin:0 0 10px">Sends to all posts where the channel is checked. Posts are sent 800ms apart.</p>';
                var bulkRow = document.createElement('div');
                bulkRow.className = 'bulk-row';
                jids.forEach(function(jidObj) {
                    var btn = document.createElement('button');
                    btn.className = 'bulk-btn';
                    btn.textContent = 'Send All \u2192 ' + jidObj.label;
                    btn.onclick = function() { sendAllToJid(jidObj, btn); };
                    bulkRow.appendChild(btn);
                });
                section.appendChild(bulkRow);
                container.appendChild(section);
            });
        </script>
    </div>
</body>
</html>`;

    try {
        // Use provided savePath or auto-generate one
        const resolvedPath = savePath
            ? savePath.replace(/^~/, process.env.HOME)
            : buildAutoPath();
        if (!fs.existsSync(resolvedPath)) {
            fs.mkdirSync(resolvedPath, { recursive: true });
        }
        const slug = `${count}_articles`;
        const redditFile = path.join(resolvedPath, `reddit_${slug}.html`);
        const xFile = path.join(resolvedPath, `x_${slug}.html`);
        const waFile = path.join(resolvedPath, `whatsapp_${slug}.html`);
        const facebookFile = path.join(resolvedPath, `facebook_${slug}.html`);

        fs.writeFileSync(redditFile, redditHtml, 'utf8');
        fs.writeFileSync(xFile, xHtml, 'utf8');
        fs.writeFileSync(waFile, waHtml, 'utf8');
        fs.writeFileSync(facebookFile, facebookHtml, 'utf8');

        res.json({
            success: true,
            savedTo: resolvedPath,
            files: { reddit: redditFile, x: xFile, whatsapp: waFile, facebook: facebookFile }
        });
    } catch (err) {
        console.error('Generate HTML error:', err);
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`Backend running on http://localhost:${PORT}`);
});
