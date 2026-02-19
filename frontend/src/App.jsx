import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = 'http://localhost:3002';

const PLATFORMS = {
    X: 'Twitter/X',
    REDDIT: 'Reddit',
    WHATSAPP: 'WhatsApp'
};

// Format a Date to local datetime-local input value
const toDatetimeLocal = (d) => {
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

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
    "Culture": "6c9fe0d6-ee85-11ee-b695-2618be2a031b",
    "History": "6c9fe0d6-ee85-11ee-b695-2618be2a031b",
    "Meetups": "ab77f80e-a5c0-11f0-afc2-12681f807942",
    "Sport": "6c9fe0d6-ee85-11ee-b695-2618be2a031b"
};

const FLAIRS = Object.keys(FLAIR_MAP);
const getSentence = (text, n = 1) => {
    const sentences = (text || '').match(/[^.!?]+[.!?]+/g) || [text || ''];
    return sentences.slice(0, n).join(' ').trim();
};

export default function App() {
    const [posts, setPosts] = useState([]);
    const [selectedPosts, setSelectedPosts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [generateResult, setGenerateResult] = useState(null);
    const [publishResult, setPublishResult] = useState(null);
    const [publishing, setPublishing] = useState(false);
    const [showDirectConfig, setShowDirectConfig] = useState(false);
    const [autoPath, setAutoPath] = useState('');
    const [selectedRange, setSelectedRange] = useState('6h');
    const [customFrom, setCustomFrom] = useState(() => toDatetimeLocal(new Date(Date.now() - 6 * 60 * 60 * 1000)));
    const [showCustom, setShowCustom] = useState(false);
    const [manualUrls, setManualUrls] = useState('');
    const [showManual, setShowManual] = useState(false);
    const [resolvingUrls, setResolvingUrls] = useState(false);
    const [showJidManager, setShowJidManager] = useState(false);
    const DEFAULT_JIDS = [
        { label: 'Broadcast Channel', jid: '0029Vb6PJDh6WaKjaAcWAX1h@newsletter', defaultOn: true },
        { label: 'News-Flash', jid: '120363269876975950@g.us', defaultOn: false },
    ];
    const [jids, setJids] = useState(() => {
        try {
            const stored = JSON.parse(localStorage.getItem('distibot_jids') || 'null');
            return (stored && stored.length) ? stored : DEFAULT_JIDS;
        } catch { return DEFAULT_JIDS; }
    });
    const [newJidLabel, setNewJidLabel] = useState('');
    const [newJidValue, setNewJidValue] = useState('');
    const [credentials, setCredentials] = useState({
        wpUrl: 'https://barna.news',
        wpUser: '',
        wpAppPassword: '',
        whapiToken: '',
        xApiKey: '',
        xApiSecret: '',
        xAccessToken: '',
        xAccessTokenSecret: '',
        redditClientId: '',
        redditClientSecret: '',
        redditUsername: '',
        redditPassword: '',
        redditSubreddit: 'BCNEnglishSpeakers',
        redditUserAgent: 'DistiBot/1.0',
        facebookPageOrGroupId: '',
        facebookAccessToken: '',
        imageDirectory: '/Users/m4owen/Library/CloudStorage/GoogleDrive-gunn0r@gmail.com/Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/10. Post Content/Default',
    });

    // Load credentials from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem('distibot_credentials');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (!parsed.wpUrl) parsed.wpUrl = 'https://barna.news';
            setCredentials(parsed);
        }
        // Fetch auto-generated save path
        axios.get(`${BACKEND_URL}/api/auto-path`).then(r => setAutoPath(r.data.path)).catch(() => { });
    }, []);

    // Save credentials to localStorage whenever they change
    useEffect(() => {
        if (credentials.wpUrl || credentials.wpUser || credentials.wpAppPassword || credentials.whapiToken) {
            localStorage.setItem('distibot_credentials', JSON.stringify(credentials));
        }
    }, [credentials]);

    // Persist JIDs
    useEffect(() => {
        localStorage.setItem('distibot_jids', JSON.stringify(jids));
    }, [jids]);

    const addJid = () => {
        if (!newJidValue.trim()) return;
        setJids(prev => [...prev, { label: newJidLabel.trim() || newJidValue.trim(), jid: newJidValue.trim(), defaultOn: true }]);
        setNewJidLabel('');
        setNewJidValue('');
    };

    const removeJid = (idx) => setJids(prev => prev.filter((_, i) => i !== idx));
    const toggleJidDefault = (idx) => setJids(prev => prev.map((j, i) => i === idx ? { ...j, defaultOn: !j.defaultOn } : j));

    const getCutoff = (range, customFromVal) => {
        if (range === '6h') return new Date(Date.now() - 6 * 60 * 60 * 1000);
        if (range === '24h') return new Date(Date.now() - 24 * 60 * 60 * 1000);
        if (range === '48h') return new Date(Date.now() - 48 * 60 * 60 * 1000);
        if (range === 'custom') return customFromVal ? new Date(customFromVal) : null;
        if (range === 'Since last check') {
            const last = localStorage.getItem('distibot_last_check');
            return last ? new Date(last) : new Date(Date.now() - 6 * 60 * 60 * 1000);
        }
        return null;
    };

    // Fetch posts from WordPress via backend
    const fetchPosts = async (rangeOverride, customFromOverride) => {
        if (!credentials.wpUrl) return;
        setLoading(true);
        const range = rangeOverride || selectedRange;
        const cfVal = customFromOverride !== undefined ? customFromOverride : customFrom;
        const cutoff = getCutoff(range, cfVal);
        try {
            const params = {
                wpUrl: credentials.wpUrl,
                wpUser: credentials.wpUser,
                wpAppPassword: credentials.wpAppPassword,
            };
            // Pass cutoff as 'after' to WP API for server-side filtering
            if (cutoff) params.after = cutoff.toISOString();
            const res = await axios.get(`${BACKEND_URL}/api/posts`, { params });
            const postsWithFlair = res.data.map(p => ({ ...p, flair: p.flair || 'News' }));
            setPosts(postsWithFlair);
            // Record this fetch time for 'Since last check'
            if (range === 'Since last check') {
                localStorage.setItem('distibot_last_check', new Date().toISOString());
            }
        } catch (err) {
            console.error('Failed to fetch posts', err);
        } finally {
            setLoading(false);
        }
    };

    // Auto-fetch on mount
    useEffect(() => {
        fetchPosts('6h');
    }, []);

    const togglePostSelection = (id) => {
        setSelectedPosts(prev =>
            prev.includes(id) ? prev.filter(pid => pid !== id) : [...prev, id]
        );
    };

    const getParsedUrls = () =>
        manualUrls.split('\n').map(u => u.trim()).filter(u => u.startsWith('http'));

    const loadManualUrls = async () => {
        const urls = getParsedUrls();
        if (!urls.length) return;
        setResolvingUrls(true);
        try {
            const res = await axios.post(`${BACKEND_URL}/api/resolve-urls`, {
                urls,
                wpUrl: credentials.wpUrl,
                wpUser: credentials.wpUser,
                wpAppPassword: credentials.wpAppPassword,
            });
            const postsWithFlair = res.data.map(p => ({ ...p, flair: p.flair || 'News' }));
            setPosts(postsWithFlair);
            setSelectedPosts(postsWithFlair.map(p => p.id));
        } catch (err) {
            console.error('Failed to resolve URLs', err);
        } finally {
            setResolvingUrls(false);
        }
    };

    const getRedditUrl = (post) => {
        const title = encodeURIComponent(post.title);
        const sentence = getSentence(post.summary, 1);
        const body = encodeURIComponent(`${sentence}\n\n${post.url}`);
        return `https://old.reddit.com/r/BCNEnglishSpeakers/submit?selftext=true&title=${title}&text=${body}`;
    };

    const getXUrl = (post) => {
        const text = encodeURIComponent(`${post.summary}\n\n${post.url}`);
        return `https://x.com/intent/post?text=${text}`;
    };

    const distributeWhatsApp = async (post) => {
        try {
            const body = `${post.summary}\n\n${post.url}`;
            // Group JID: 120363269876975950@g.us
            // Broadcast Channel JID: 0029Vb6PJDh6WaKjaAcWAX1h@newsletter

            const targets = ['120363269876975950@g.us', '0029Vb6PJDh6WaKjaAcWAX1h@newsletter'];

            for (const to of targets) {
                await axios.post(`${BACKEND_URL}/api/whatsapp/distribute`, {
                    token: credentials.whapiToken,
                    to,
                    body
                });
            }
            alert('WhatsApp distribution triggered!');
        } catch (err) {
            console.error('WhatsApp distribution failed', err);
        }
    };

    const handleDistribute = () => {
        const selected = posts.filter(p => selectedPosts.includes(p.id));
        selected.forEach(post => {
            window.open(getRedditUrl(post), '_blank');
            window.open(getXUrl(post), '_blank');
            distributeWhatsApp(post);
        });
    };

    const updatePostFlair = (postId, newFlair) => {
        setPosts(prev => prev.map(p => p.id === postId ? { ...p, flair: newFlair } : p));
    };

    const handleSummarizeSelection = async () => {
        const selected = posts.filter(p => selectedPosts.includes(p.id));
        if (!selected.length) { alert('No posts to summarize.'); return; }
        setGenerating(true);
        try {
            const sumRes = await axios.post(`${BACKEND_URL}/api/summarize`, { posts: selected });
            const map = {};
            sumRes.data.summaries.forEach(s => { map[s.id] = s; });

            setPosts(prev => prev.map(p => {
                const match = map[p.id];
                if (match) {
                    return { ...p, summary: match.summary, flair: match.flair, summarized: true };
                }
                return p;
            }));
        } catch (err) {
            alert('Summarization failed: ' + (err.response?.data?.error || err.message));
        } finally {
            setGenerating(false);
        }
    };

    const pickFolder = async () => {
        try {
            const { ipcRenderer } = window.require('electron');
            const folder = await ipcRenderer.invoke('pick-folder');
            if (folder) setSavePath(folder);
        } catch {
            alert('Folder picker only works in the Electron app. Please type the path manually.');
        }
    };

    const openFolder = async (folderPath) => {
        try {
            await axios.post(`${BACKEND_URL}/api/open-folder`, { folderPath });
        } catch {
            alert('Could not open folder: ' + folderPath);
        }
    };

    const handleGenerateHtml = async () => {
        const selected = selectedPosts.length > 0
            ? posts.filter(p => selectedPosts.includes(p.id))
            : posts;
        if (!selected.length) { alert('No posts to generate.'); return; }
        setGenerating(true);
        setGenerateResult(null);
        const unsummarized = selected.filter(p => !p.summarized);
        if (unsummarized.length > 0) {
            if (!confirm(`Warning: ${unsummarized.length} posts haven't been summarized with AI yet. Generate anyway using defaults?`)) {
                setGenerating(false);
                return;
            }
        }
        try {
            const res = await axios.post(`${BACKEND_URL}/api/generate-html`, {
                posts: selected,
                whapiToken: credentials.whapiToken,
                jids
            });
            // Refresh auto-path for next batch
            axios.get(`${BACKEND_URL}/api/auto-path`).then(r => setAutoPath(r.data.path)).catch(() => { });
            setGenerateResult({ success: true, savedTo: res.data.savedTo, files: res.data.files });
        } catch (err) {
            setGenerateResult({ success: false, error: err.response?.data?.error || err.message });
        } finally {
            setGenerating(false);
        }
    };

    const handleGenerateAndSubmit = async () => {
        const selected = selectedPosts.length > 0
            ? posts.filter(p => selectedPosts.includes(p.id))
            : posts;
        if (!selected.length) { alert('No posts selected.'); return; }

        setGenerating(true);
        setPublishing(true);
        setGenerateResult(null);
        setPublishResult(null);
        try {
            const htmlRes = await axios.post(`${BACKEND_URL}/api/generate-html`, {
                posts: selected,
                whapiToken: credentials.whapiToken,
                jids
            });
            setGenerateResult({ success: true, savedTo: htmlRes.data.savedTo, files: htmlRes.data.files });

            const publishRes = await axios.post(`${BACKEND_URL}/api/distribute-direct`, {
                posts: selected,
                credentials,
                jids,
                imageDirectory: credentials.imageDirectory
            });
            setPublishResult({
                success: true,
                processedPosts: publishRes.data.processedPosts,
                platformSuccessCount: publishRes.data.platformSuccessCount,
                results: publishRes.data.results
            });

            axios.get(`${BACKEND_URL}/api/auto-path`).then(r => setAutoPath(r.data.path)).catch(() => { });
        } catch (err) {
            setPublishResult({
                success: false,
                error: err.response?.data?.error || err.message
            });
        } finally {
            setGenerating(false);
            setPublishing(false);
        }
    };

    return (
        <div className="min-h-screen pb-[420px]">
            {/* Header & Navigation */}
            <header className="sticky top-0 z-30 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-primary/10">
                <div className="flex items-center p-4 justify-between">
                    <div className="flex items-center gap-3">
                        <span className="material-symbols-outlined text-primary">hub</span>
                        <h1 className="text-lg font-bold tracking-tight">DistiBot</h1>
                    </div>
                    <div className="flex gap-4 items-center">
                        <input
                            type="text"
                            placeholder="WP URL"
                            className="text-xs p-1 rounded border bg-transparent"
                            value={credentials.wpUrl}
                            onChange={(e) => setCredentials({ ...credentials, wpUrl: e.target.value })}
                        />
                        <button onClick={fetchPosts} className="p-2 rounded-full hover:bg-primary/10 transition-colors">
                            <span className="material-symbols-outlined text-primary">refresh</span>
                        </button>
                    </div>
                </div>

                {/* Time Range Selector */}
                <div className="flex gap-2 px-4 pb-2 overflow-x-auto no-scrollbar">
                    {['6h', '24h', '48h', 'Since last check', 'Custom'].map((label) => (
                        <button key={label} onClick={() => {
                            const r = label === 'Custom' ? 'custom' : label;
                            setSelectedRange(r);
                            setShowCustom(label === 'Custom');
                            if (label !== 'Custom') fetchPosts(r);
                        }} className={`flex h-9 shrink-0 items-center justify-center rounded-full px-5 text-sm font-medium ${selectedRange === (label === 'Custom' ? 'custom' : label)
                            ? 'bg-primary text-white'
                            : 'bg-primary/10 text-primary border border-primary/20'
                            }`}>
                            {label}
                        </button>
                    ))}
                </div>

                {/* Custom datetime picker */}
                {showCustom && (
                    <div className="flex gap-2 px-4 pb-3 items-center">
                        <span className="text-xs text-slate-500 shrink-0">From:</span>
                        <input
                            type="datetime-local"
                            className="flex-1 text-xs p-1.5 border rounded-lg dark:bg-slate-800 dark:border-slate-700"
                            value={customFrom}
                            onChange={e => setCustomFrom(e.target.value)}
                        />
                        <button
                            onClick={() => fetchPosts('custom', customFrom)}
                            className="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg bg-primary text-white"
                        >
                            Fetch
                        </button>
                    </div>
                )}

                {/* Manual URL entry toggle */}
                <div className="flex gap-2 px-4 pb-3">
                    <button
                        onClick={() => setShowManual(v => !v)}
                        className={`flex h-8 items-center gap-1 rounded-full px-4 text-xs font-medium ${showManual ? 'bg-primary text-white' : 'bg-primary/10 text-primary border border-primary/20'
                            }`}
                    >
                        <span className="material-symbols-outlined text-sm">edit</span>
                        Manual URLs
                    </button>
                </div>

                {showManual && (
                    <div className="px-4 pb-3">
                        <textarea
                            rows={4}
                            placeholder="Paste one URL per line\nhttps://barna.news/article-1/\nhttps://barna.news/article-2/"
                            className="w-full text-xs p-2 border rounded-lg dark:bg-slate-800 dark:border-slate-700 font-mono resize-none"
                            value={manualUrls}
                            onChange={e => setManualUrls(e.target.value)}
                        />
                        <button
                            onClick={loadManualUrls}
                            disabled={resolvingUrls || !getParsedUrls().length}
                            className="mt-1 text-xs font-medium px-3 py-1.5 rounded-lg bg-primary text-white disabled:opacity-50 flex items-center gap-1"
                        >
                            {resolvingUrls
                                ? <><span className="animate-spin material-symbols-outlined text-sm">progress_activity</span> Fetching…</>
                                : `Load ${getParsedUrls().length} URLs`
                            }
                        </button>
                    </div>
                )}
            </header>

            {/* Main Content: Post List */}
            <main className="p-4 space-y-4">
                <div className="flex items-center justify-between mb-2">
                    <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                        Published Posts ({posts.length})
                    </h2>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setSelectedPosts(posts.map(p => p.id))}
                            className="text-xs font-medium text-primary flex items-center gap-1"
                        >
                            Select All <span className="material-symbols-outlined text-xs">select_all</span>
                        </button>
                        {selectedPosts.length > 0 && (
                            <button
                                onClick={() => setSelectedPosts([])}
                                className="text-xs font-medium text-slate-400 flex items-center gap-1"
                            >
                                Deselect All <span className="material-symbols-outlined text-xs">deselect</span>
                            </button>
                        )}
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center p-10">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {posts.map(post => {
                            const isSelected = selectedPosts.includes(post.id);
                            return (
                                <div
                                    key={post.id}
                                    onClick={() => togglePostSelection(post.id)}
                                    className={`group relative flex items-center gap-4 rounded-xl bg-white dark:bg-slate-900 p-3 shadow-sm cursor-pointer border-2 transition-all ${isSelected ? 'border-primary' : 'border-transparent'}`}
                                >
                                    <div className="relative w-24 h-24 shrink-0 overflow-hidden rounded-lg bg-slate-200">
                                        <img className="w-full h-full object-cover" src={post.featuredImage || 'https://via.placeholder.com/150'} alt={post.title} />
                                    </div>
                                    <div className="flex flex-col flex-1 gap-1">
                                        <div className="flex justify-between items-start">
                                            <div className="flex flex-col">
                                                <span className={`text-[10px] font-bold uppercase ${isSelected ? 'text-primary' : 'text-slate-400'}`}>Category</span>
                                                <select
                                                    value={post.flair || 'News'}
                                                    onClick={(e) => e.stopPropagation()}
                                                    onChange={(e) => updatePostFlair(post.id, e.target.value)}
                                                    className={`mt-1 text-[11px] font-bold py-1 px-2 rounded-md border ${isSelected ? 'border-primary bg-primary/5 text-primary' : 'border-slate-200 bg-slate-50 text-slate-500'}`}
                                                >
                                                    {FLAIRS.map(f => <option key={f} value={f}>{f}</option>)}
                                                </select>
                                            </div>
                                            <span className="text-[10px] text-slate-400 font-mono">#{post.id}</span>
                                        </div>
                                        <h3 className="text-sm font-bold leading-tight line-clamp-2 mt-2">{post.title}</h3>
                                        {post.summarized && (
                                            <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-100 dark:border-blue-900/30">
                                                <p className="text-[11px] leading-snug italic text-blue-900 dark:text-blue-200">"{post.summary}"</p>
                                                <div className="flex justify-between items-center mt-1">
                                                    <span className="text-[9px] font-bold text-blue-400 uppercase tracking-widest">AI Summary</span>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setPosts(prev => prev.map(p => p.id === post.id ? { ...p, summarized: false } : p));
                                                        }}
                                                        className="text-[9px] font-bold text-red-400 hover:text-red-600 transition-colors"
                                                    >
                                                        Reset
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                        <p className="text-xs text-slate-500 mt-1">{new Date(post.date).toLocaleDateString()}</p>
                                        <div className="mt-2 flex items-center">
                                            <span className={`material-symbols-outlined text-lg ${isSelected ? 'text-primary' : 'text-slate-300'}`} style={{ fontVariationSettings: isSelected ? "'FILL' 1" : "" }}>
                                                {isSelected ? 'check_box' : 'check_box_outline_blank'}
                                            </span>
                                            <span className={`text-xs ml-1 ${isSelected ? 'font-semibold text-primary' : 'font-medium text-slate-400'}`}>
                                                {isSelected ? 'Selected' : 'Select'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* Bottom Action Bar */}
            <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white dark:bg-slate-900 border-t border-primary/10 shadow-[0_-8px_30px_rgb(0,0,0,0.12)]">
                <div className="flex items-center justify-between mb-4 px-2">
                    <div className="flex items-center gap-4">
                        {/* Platform Indicators */}
                        <div className="flex flex-col items-center gap-1">
                            <div className="relative flex items-center justify-center size-10 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-primary">
                                <span className="material-symbols-outlined text-slate-900 dark:text-white text-xl">brand_family</span>
                                <div className="absolute -top-1 -right-1 bg-primary text-white rounded-full size-4 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: "'wght' 700" }}>check</span>
                                </div>
                            </div>
                            <span className="text-[10px] font-bold text-primary">X/Twitter</span>
                        </div>

                        <div className="flex flex-col items-center gap-1">
                            <div className="relative flex items-center justify-center size-10 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-primary">
                                <span className="material-symbols-outlined text-orange-500 text-xl">forum</span>
                                <div className="absolute -top-1 -right-1 bg-primary text-white rounded-full size-4 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: "'wght' 700" }}>check</span>
                                </div>
                            </div>
                            <span className="text-[10px] font-bold text-primary">Reddit</span>
                        </div>

                        <div className="flex flex-col items-center gap-1">
                            <div className="relative flex items-center justify-center size-10 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-primary">
                                <span className="material-symbols-outlined text-green-500 text-xl">chat</span>
                                <div className="absolute -top-1 -right-1 bg-primary text-white rounded-full size-4 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: "'wght' 700" }}>check</span>
                                </div>
                            </div>
                            <span className="text-[10px] font-bold text-primary">WhatsApp</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <p className="text-[10px] font-bold text-slate-400 uppercase">Selected</p>
                        <p className="text-lg font-bold text-primary">{selectedPosts.length} Posts</p>
                    </div>
                </div>

                {/* WhAPI Config Row */}
                <div className="flex gap-2 mb-2 items-center">
                    <input
                        type="text"
                        placeholder="WhAPI Token"
                        className="flex-1 text-xs p-2 border rounded-lg dark:bg-slate-800 dark:border-slate-700 font-mono"
                        value={credentials.whapiToken}
                        onChange={e => setCredentials({ ...credentials, whapiToken: e.target.value })}
                    />
                    <button
                        onClick={() => setShowJidManager(v => !v)}
                        className={`shrink-0 flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg border transition-colors ${showJidManager ? 'bg-green-600 text-white border-green-600' : 'border-green-600/40 text-green-700 hover:bg-green-50'
                            }`}
                    >
                        <span className="material-symbols-outlined text-base">group</span>
                        Channels ({jids.length})
                    </button>
                    <button
                        onClick={() => setShowDirectConfig(v => !v)}
                        className={`shrink-0 flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg border transition-colors ${showDirectConfig ? 'bg-blue-600 text-white border-blue-600' : 'border-blue-600/40 text-blue-700 hover:bg-blue-50'
                            }`}
                    >
                        <span className="material-symbols-outlined text-base">settings</span>
                        Direct APIs
                    </button>
                </div>

                {showDirectConfig && (
                    <div className="mb-3 border border-blue-200 rounded-xl p-3 bg-blue-50 dark:bg-blue-900/10 space-y-2">
                        <p className="text-[10px] font-bold uppercase text-blue-700">Direct Publish Credentials</p>
                        <input type="text" placeholder="X API Key" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.xApiKey} onChange={e => setCredentials({ ...credentials, xApiKey: e.target.value })} />
                        <input type="text" placeholder="X API Secret" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.xApiSecret} onChange={e => setCredentials({ ...credentials, xApiSecret: e.target.value })} />
                        <input type="text" placeholder="X Access Token" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.xAccessToken} onChange={e => setCredentials({ ...credentials, xAccessToken: e.target.value })} />
                        <input type="text" placeholder="X Access Token Secret" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.xAccessTokenSecret} onChange={e => setCredentials({ ...credentials, xAccessTokenSecret: e.target.value })} />
                        <input type="text" placeholder="Reddit Client ID" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditClientId} onChange={e => setCredentials({ ...credentials, redditClientId: e.target.value })} />
                        <input type="text" placeholder="Reddit Client Secret" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditClientSecret} onChange={e => setCredentials({ ...credentials, redditClientSecret: e.target.value })} />
                        <input type="text" placeholder="Reddit Username" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditUsername} onChange={e => setCredentials({ ...credentials, redditUsername: e.target.value })} />
                        <input type="password" placeholder="Reddit Password" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditPassword} onChange={e => setCredentials({ ...credentials, redditPassword: e.target.value })} />
                        <input type="text" placeholder="Reddit Subreddit" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditSubreddit} onChange={e => setCredentials({ ...credentials, redditSubreddit: e.target.value })} />
                        <input type="text" placeholder="Reddit User-Agent" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.redditUserAgent} onChange={e => setCredentials({ ...credentials, redditUserAgent: e.target.value })} />
                        <input type="text" placeholder="Facebook Page/Group ID" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.facebookPageOrGroupId} onChange={e => setCredentials({ ...credentials, facebookPageOrGroupId: e.target.value })} />
                        <input type="text" placeholder="Facebook Access Token" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.facebookAccessToken} onChange={e => setCredentials({ ...credentials, facebookAccessToken: e.target.value })} />
                        <input type="text" placeholder="Fallback Image Directory" className="w-full text-xs p-2 border rounded-lg font-mono" value={credentials.imageDirectory} onChange={e => setCredentials({ ...credentials, imageDirectory: e.target.value })} />
                    </div>
                )}

                {/* JID Manager */}
                {showJidManager && (
                    <div className="mb-3 border border-green-200 rounded-xl p-3 bg-green-50 dark:bg-green-900/10 space-y-2">
                        <p className="text-[10px] font-bold uppercase text-green-700">WhatsApp Channels &amp; Groups</p>
                        {jids.length === 0 && (
                            <p className="text-xs text-slate-400">No channels added yet.</p>
                        )}
                        {jids.map((j, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                                <button
                                    onClick={() => toggleJidDefault(idx)}
                                    title={j.defaultOn ? 'Default: ON (pre-checked in HTML)' : 'Default: OFF (unchecked in HTML)'}
                                    className={`shrink-0 text-xs font-bold px-2 py-1 rounded border transition-colors ${j.defaultOn
                                        ? 'bg-green-600 text-white border-green-600'
                                        : 'bg-white text-slate-400 border-slate-300'
                                        }`}
                                >
                                    {j.defaultOn ? 'ON' : 'OFF'}
                                </button>
                                <span className="flex-1 text-xs font-mono bg-white dark:bg-slate-800 border rounded px-2 py-1 truncate">
                                    <span className="font-semibold text-green-700">{j.label}</span>
                                    <span className="text-slate-400 ml-1 text-[10px]">{j.jid}</span>
                                </span>
                                <button onClick={() => removeJid(idx)} className="shrink-0 text-red-400 hover:text-red-600">
                                    <span className="material-symbols-outlined text-base">delete</span>
                                </button>
                            </div>
                        ))}
                        <p className="text-[10px] text-slate-400 pt-1">ON = pre-checked in generated HTML. Toggle per-post in the HTML before sending.</p>
                        <div className="flex gap-1 pt-1">
                            <input
                                type="text"
                                placeholder="Label (e.g. BCN Group)"
                                className="w-28 text-xs p-1.5 border rounded-lg dark:bg-slate-800 dark:border-slate-700"
                                value={newJidLabel}
                                onChange={e => setNewJidLabel(e.target.value)}
                            />
                            <input
                                type="text"
                                placeholder="JID (e.g. 120363...@g.us)"
                                className="flex-1 text-xs p-1.5 border rounded-lg dark:bg-slate-800 dark:border-slate-700 font-mono"
                                value={newJidValue}
                                onChange={e => setNewJidValue(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && addJid()}
                            />
                            <button
                                onClick={addJid}
                                disabled={!newJidValue.trim()}
                                className="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg bg-green-600 text-white disabled:opacity-40"
                            >
                                Add
                            </button>
                        </div>
                    </div>
                )}

                {/* Auto Save Path Display */}
                <div className="flex gap-2 mb-3 items-center">
                    <span className="material-symbols-outlined text-slate-400 text-base shrink-0">folder</span>
                    <span className="flex-1 text-[11px] font-mono text-slate-500 dark:text-slate-400 truncate" title={autoPath}>
                        {autoPath || 'Calculating save path…'}
                    </span>
                </div>

                {/* Generate Result */}
                {generateResult && (
                    <div className={`text-xs rounded-lg px-3 py-2 mb-3 ${generateResult.success ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
                        {generateResult.success ? (
                            <div className="flex items-center justify-between gap-2">
                                <span className="truncate">✓ <span className="font-mono">{generateResult.savedTo.split('/').slice(-3).join('/')}</span></span>
                                <button
                                    onClick={() => openFolder(generateResult.savedTo)}
                                    className="shrink-0 flex items-center gap-1 font-semibold px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
                                >
                                    <span className="material-symbols-outlined text-sm">folder_open</span>
                                    Open
                                </button>
                            </div>
                        ) : (
                            <span>✗ {generateResult.error}</span>
                        )}
                    </div>
                )}

                {publishResult && (
                    <div className={`text-xs rounded-lg px-3 py-2 mb-3 ${publishResult.success ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
                        {publishResult.success ? (
                            <span>✓ Published {publishResult.platformSuccessCount} platform actions across {publishResult.processedPosts} posts</span>
                        ) : (
                            <span>✗ Direct publish failed: {publishResult.error}</span>
                        )}
                    </div>
                )}

                {/* Action Buttons Row */}
                <div className="flex gap-4 mb-3">
                    <button
                        onClick={handleSummarizeSelection}
                        disabled={generating || !selectedPosts.length}
                        className="flex-1 h-12 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 border border-slate-200 dark:border-slate-700 active:scale-[0.98] transition-all disabled:opacity-50"
                    >
                        <span className="material-symbols-outlined">{generating ? 'progress_activity' : 'smart_toy'}</span>
                        {generating ? 'Processing…' : `AI Summarize (${selectedPosts.length} Posts)`}
                    </button>

                    <button
                        onClick={handleGenerateHtml}
                        disabled={generating || publishing}
                        className="flex-[2] h-12 bg-primary text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-primary/30 active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale"
                    >
                        <span className="material-symbols-outlined">{generating ? 'hourglass_top' : 'download'}</span>
                        {generating ? 'Finalizing…' : `Generate HTML Files (${selectedPosts.length > 0 ? selectedPosts.length : posts.length})`}
                    </button>

                    <button
                        onClick={handleGenerateAndSubmit}
                        disabled={generating || publishing}
                        className="flex-[2] h-12 bg-green-600 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-green-600/30 active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale"
                    >
                        <span className="material-symbols-outlined">{publishing ? 'upload' : 'send'}</span>
                        {publishing ? 'Publishing…' : `Generate + Submit (${selectedPosts.length > 0 ? selectedPosts.length : posts.length})`}
                    </button>
                </div>
            </div>
        </div>
    );
}
