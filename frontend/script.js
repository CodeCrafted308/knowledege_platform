const API_BASE_URL = 'http://127.0.0.1:8000/api';
const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';
const THEME_KEY = 'siteTheme';
const CHAT_THEME_KEY = 'chatTheme';

let currentUser = null;
let profileViewUser = null;
let currentTheme = 'light';
let currentChatTheme = 'theme-blue';
let challengeMode = false;
let currentThreadRoot = null;
let lastKnowledgeSuggestion = null;
let knowledgeSuggestionTimer = null;

// Carousel variables
let carouselIndex = 0;
let carouselIntervalId = null;
const carouselImages = [
    'https://img.freepik.com/premium-photo/professional-business-woman-working-office_969354-3132.jpg',
    'https://www.wcwonline.org/images/stories/researchandaction/Spring2018/diverse-professional-women-working.jpg',
    'https://static1.bigstockphoto.com/0/4/1/large1500/140428673.jpg',
    'https://www.yorku.ca/edu/wp-content/uploads/sites/28/2020/08/Research-stories_shutterstock_124494247-1024x960.jpg',
    'https://tse4.mm.bing.net/th/id/OIP.OZlGsiysjkBGew-6f2VGAQHaE7?rs=1&pid=ImgDetMain&o=7&rm=3'
];


window.addEventListener('DOMContentLoaded', initApp);

function initApp() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const createPostForm = document.getElementById('createPostForm');

    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (registerForm) registerForm.addEventListener('submit', handleRegister);
    if (createPostForm) createPostForm.addEventListener('submit', handleCreatePost);

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                performSearch();
            }
        });
    }

    const savedUser = localStorage.getItem(AUTH_USER_KEY);
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
    }

    initializeTheme();
    fetchCurrentUser();
    showHome();
}

function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function encodeSvgData(svg) {
    return window.btoa(unescape(encodeURIComponent(svg)));
}

function getAvatarFallbackSvg(name, size = 128) {
    const initials = (name || 'U')
        .split(' ')
        .filter(Boolean)
        .map(part => part.charAt(0))
        .slice(0, 2)
        .join('')
        .toUpperCase() || 'U';
    const fontSize = Math.floor(size * 0.45);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}"><rect width="100%" height="100%" rx="${Math.floor(size * 0.25)}" fill="#8b5cf6"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Inter, sans-serif" font-size="${fontSize}" font-weight="700" fill="#ffffff">${initials}</text></svg>`;
    return `data:image/svg+xml;base64,${encodeSvgData(svg)}`;
}

function getProfileAvatarUrl(profilePicture, name) {
    if (profilePicture && typeof profilePicture === 'string' && profilePicture.trim() !== '') {
        return profilePicture;
    }
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(name || 'User')}&background=8b5cf6&color=fff&size=128`;
}

function saveAuthToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function saveCurrentUser(user) {
    currentUser = user;
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

function clearAuthData() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    currentUser = null;
}

async function fetchCurrentUser() {
    const token = getAuthToken();
    if (!token) {
        updateAuthUI(false);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (!response.ok) {
            clearAuthData();
            updateAuthUI(false);
            return;
        }

        const user = await response.json();
        saveCurrentUser(user);
        updateAuthUI(true);
    } catch (error) {
        console.error('Unable to validate user', error);
        clearAuthData();
        updateAuthUI(false);
    }
}

function updateAuthUI(isLoggedIn) {
    const authPanel = document.getElementById('navAuth');
    const userPanel = document.getElementById('navUser');
    const navUsername = document.getElementById('navUsername');
    const navUserAvatar = document.getElementById('navUserAvatar');
    const navAdminLink = document.getElementById('navAdminLink');

    if (isLoggedIn && currentUser) {
        authPanel.style.display = 'none';
        userPanel.style.display = 'flex';
        navUsername.textContent = currentUser.full_name || currentUser.username || 'Member';
        if (navUserAvatar) {
            navUserAvatar.src = currentUser.profile_picture || 'https://picsum.photos/seed/user/40/40.jpg';
        }
        if (navAdminLink) {
            navAdminLink.style.display = currentUser.is_admin ? 'inline-flex' : 'none';
        }
    } else {
        authPanel.style.display = 'flex';
        userPanel.style.display = 'none';
        if (navUserAvatar) {
            navUserAvatar.src = 'https://picsum.photos/seed/user/40/40.jpg';
        }
        if (navAdminLink) {
            navAdminLink.style.display = 'none';
        }
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(currentTheme);
}

function setTheme(theme) {
    const body = document.body;
    const toggleButton = document.getElementById('themeToggleButton');
    currentTheme = theme;
    localStorage.setItem(THEME_KEY, theme);

    if (theme === 'dark') {
        body.classList.add('dark-mode');
        if (toggleButton) {
            toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        }
    } else {
        body.classList.remove('dark-mode');
        if (toggleButton) {
            toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        }
    }
}

function initializeTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    setTheme(savedTheme === 'dark' ? 'dark' : 'light');
}

function initializeChatTheme() {
    const savedChatTheme = localStorage.getItem(CHAT_THEME_KEY);
    setChatTheme(savedChatTheme || currentChatTheme, false);
}

function setChatTheme(theme, save = true) {
    const chatPage = document.getElementById('chatPage');
    if (!chatPage) return;
    chatPage.classList.remove('theme-blue', 'theme-emerald', 'theme-purple', 'theme-sunset', 'theme-midnight');
    chatPage.classList.add(theme);
    currentChatTheme = theme;
    if (save) {
        localStorage.setItem(CHAT_THEME_KEY, theme);
    }
}

function startCarousel() {
    const carouselImage = document.getElementById('carouselImage');
    if (!carouselImage) return;

    if (carouselIntervalId) {
        clearInterval(carouselIntervalId);
    }

    carouselIntervalId = setInterval(() => {
        carouselIndex = (carouselIndex + 1) % carouselImages.length;
        updateCarousel();
    }, 5000);

    updateCarousel();
}

function stopCarousel() {
    if (carouselIntervalId) {
        clearInterval(carouselIntervalId);
        carouselIntervalId = null;
    }
}

function updateCarousel() {
    const carouselImage = document.getElementById('carouselImage');
    const indicators = document.querySelectorAll('.indicator');

    if (carouselImage) {
        carouselImage.src = carouselImages[carouselIndex];
    }

    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === carouselIndex);
    });
}

function jumpToCarouselSlide(index) {
    carouselIndex = index;
    updateCarousel();

    if (carouselIntervalId) {
        clearInterval(carouselIntervalId);
    }

    carouselIntervalId = setInterval(() => {
        carouselIndex = (carouselIndex + 1) % carouselImages.length;
        updateCarousel();
    }, 5000);
}

function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => {
        page.style.display = page.id === pageId ? 'block' : 'none';
    });
}

function setActiveNav(activeId) {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    const activeLink = document.getElementById(activeId);
    if (activeLink) activeLink.classList.add('active');
}

function hideAllPages() {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => {
        page.style.display = 'none';
    });
}

function updateActiveNavLink(activeId) {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    const activeLink = document.getElementById(activeId);
    if (activeLink) activeLink.classList.add('active');
}

function showHome(event) {
    if (event) event.preventDefault();
    showPage('homePage');
    setActiveNav('navHomeLink');
    startCarousel();
}

function showFeed(event) {
    if (event) event.preventDefault();
    hideAllPages();
    document.getElementById('feedPage').style.display = 'block';
    loadPosts();
    //loadTopContributors();
    updateActiveNavLink('feedLink');
}

function showAboutUs(event) {
    if (event) event.preventDefault();
    showPage('aboutUsPage');
    setActiveNav('navAboutLink');
    stopCarousel();
}

function showCreatePost(event) {
    if (event) event.preventDefault();
    stopCarousel();
    if (!getAuthToken()) {
        showToast('Please log in first to create a post.', 'warning');
        showLogin();
        return;
    }

    showPage('createPostPage');
    setActiveNav('navCreatePostLink');
}

function showConnections(event) {
    if (event) event.preventDefault();
    showPage('connectionsPage');
    setActiveNav('navConnectionsLink');
    renderConnections();
}

function showChat(event) {
    if (event) event.preventDefault();
    if (!getAuthToken()) {
        showToast('Please log in first to chat.', 'warning');
        showLogin();
        return;
    }
    showPage('chatPage');
    setActiveNav('navChatLink');
    initializeChat();
}

function searchChatUsers() {
    const query = document.getElementById('chatUserSearchInput').value.trim();
    if (!query) {
        document.getElementById('chatUserSearchResults').innerHTML = '<p class="empty-state">Enter a name or username to search for people.</p>';
        return;
    }

    fetch(`${API_BASE_URL}/users?q=${encodeURIComponent(query)}&limit=20`, {
        headers: {
            Authorization: `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(users => {
        renderChatUserSearchResults(Array.isArray(users) ? users : []);
    })
    .catch(error => {
        console.error('Search chat users failed:', error);
        document.getElementById('chatUserSearchResults').innerHTML = '<p class="empty-state">Unable to search users right now.</p>';
    });
}

function renderChatUserSearchResults(users) {
    const container = document.getElementById('chatUserSearchResults');
    container.innerHTML = '';

    if (!Array.isArray(users) || users.length === 0) {
        container.innerHTML = '<p class="empty-state">No users found. Try a different name.</p>';
        return;
    }

    container.innerHTML = users.map(user => `
        <div class="search-user-card card">
            <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.username)}&background=8b5cf6&color=fff&size=128" alt="${user.full_name || user.username}" class="search-user-avatar" onerror="this.onerror=null;this.src='${getAvatarFallbackSvg(user.full_name || user.username)}';" />
            <div>
                <strong onclick="showUserProfile('${user.id}')" style="cursor: pointer; color: var(--primary-color);">${user.full_name || user.username}</strong>
                <span class="user-handle">@${user.username}</span>
                <p>${user.reliability_score?.toFixed(1) ?? 0}% reliable</p>
            </div>
            ${currentUser && user.id !== currentUser.id && getAuthToken() ? `<button class="btn btn-primary btn-small" onclick="messageUser('${user.id}','${user.full_name || user.username}')"><i class="fas fa-comment"></i> Message</button>` : ''}
        </div>
    `).join('');
}

function messageUser(userId, userName) {
    if (!getAuthToken()) {
        showToast('Please log in first to send messages.', 'warning');
        showLogin();
        return;
    }

    currentChatUser = { id: userId, name: userName || 'User' };
    showPage('chatPage');
    setActiveNav('navChatLink');
    setChatHeader(userName || 'Chat');
    showChatInput(true);
    loadConversations();
    loadConversation(userId);
}

function setChatHeader(userName) {
    const chatHeader = document.getElementById('chatHeader');
    if (chatHeader) {
        chatHeader.innerHTML = `<h3>Chatting with ${userName}</h3>`;
    }
}

function showChatInput(show = true) {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.style.display = show ? 'flex' : 'none';
    }
}

function openAdminPanel(event) {
    if (event) event.preventDefault();
    window.location.href = 'admin.html';
}

function showProfile(event, userId = null) {
    if (event) event.preventDefault();
    stopCarousel();
    if (userId) {
        showUserProfile(userId);
        return;
    }

    if (!getAuthToken()) {
        showToast('Please log in to view your profile.', 'warning');
        showLogin();
        return;
    }

    profileViewUser = null;
    showPage('profilePage');
    setActiveNav('navProfileLink');
    renderProfile();
}

async function showUserProfile(userId) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/users/${userId}`);
        if (!response.ok) {
            showToast('Unable to load user profile.', 'error');
            return;
        }

        profileViewUser = await response.json();
        showPage('profilePage');
        setActiveNav('navProfileLink');
        renderProfile();
    } catch (error) {
        console.error('Show user profile failed', error);
        showToast('Unable to load profile now.', 'error');
    } finally {
        showLoading(false);
    }
}

function showLogin(event) {
    if (event) event.preventDefault();
    stopCarousel();
    showPage('loginPage');
    setActiveNav('');
}

function showRegister(event) {
    if (event) event.preventDefault();
    stopCarousel();
    showPage('registerPage');
    setActiveNav('');
}

function showConnections(event) {
    if (event) event.preventDefault();
    showPage('connectionsPage');
    setActiveNav('navConnectionsLink');
    renderConnections();
}

async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    if (!email || !password) {
        showToast('Please enter both email and password.', 'error');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Login failed', 'error');
            return;
        }

        const data = await response.json();
        saveAuthToken(data.access_token);
        saveCurrentUser(data.user);
        updateAuthUI(true);
        showToast('Logged in successfully!', 'success');
        showHome();
    } catch (error) {
        console.error('Login failed', error);
        showToast('Unable to login. Check your connection.', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById('registerUsername').value.trim();
    const fullName = document.getElementById('registerFullName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();

    if (!username || !fullName || !email || !password) {
        showToast('Please complete all registration fields.', 'error');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, full_name: fullName, password })
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Registration failed', 'error');
            return;
        }

        showToast('Registration successful. Please sign in.', 'success');
        showLogin();
    } catch (error) {
        console.error('Registration failed', error);
        showToast('Unable to register. Check your connection.', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleCreatePost(event) {
    event.preventDefault();

    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();
    const postType = document.getElementById('postType').value;
    const fileInput = document.getElementById('postFile');
    const files = Array.from(fileInput.files || []);

    if (!title || !content) {
        showToast('Please add a title and some content.', 'error');
        return;
    }

    const token = getAuthToken();
    if (!token) {
        showToast('Please log in first.', 'warning');
        showLogin();
        return;
    }

    try {
        showLoading(true);

        let response;
        if (files.length > 0) {
            // Use FormData for file uploads
            const formData = new FormData();
            formData.append('title', title);
            formData.append('content', content);
            formData.append('post_type', postType);
            formData.append('tags', '');
            files.forEach(file => {
                formData.append('files', file);
            });

            response = await fetch(`${API_BASE_URL}/posts/with-file`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`
                    // Don't set Content-Type for FormData
                },
                body: formData
            });
        } else {
            // Use JSON for text-only posts
            response = await fetch(`${API_BASE_URL}/posts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ title, content, post_type: postType, tags: [] })
            });
        }

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Could not publish post', 'error');
            return;
        }

        document.getElementById('postTitle').value = '';
        document.getElementById('postContent').value = '';
        document.getElementById('postType').value = 'text';
        document.getElementById('postFile').value = '';
        const fileStatusEl = document.getElementById('fileStatus');
        if (fileStatusEl) {
            fileStatusEl.textContent = 'Attach Media';
        }

        showToast('Post created successfully!', 'success');
        showHome();
    } catch (error) {
        console.error('Create post failed', error);
        showToast('Unable to publish post right now.', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleQuickPost() {
    const content = document.getElementById('quickPostContent').value.trim();
    const fileInput = document.getElementById('quickPostFile');
    const files = Array.from(fileInput.files || []);

    if (!content && files.length === 0) {
        showToast('Please enter text or attach a file.', 'error');
        return;
    }

    if (!getAuthToken()) {
        showToast('Please log in first to share knowledge.', 'warning');
        showLogin();
        return;
    }

    try {
        showLoading(true);

        let response;
        if (files.length > 0) {
            // Use FormData for file uploads
            const formData = new FormData();
            formData.append('title', 'Quick Knowledge Share');
            formData.append('content', content || 'Check out this media!');
            formData.append('post_type', 'text');
            formData.append('tags', '');
            files.forEach(file => {
                formData.append('files', file);
            });

            response = await fetch(`${API_BASE_URL}/posts/with-file`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${getAuthToken()}`
                    // Don't set Content-Type for FormData
                },
                body: formData
            });
        } else {
            // Use JSON for text-only posts
            response = await fetch(`${API_BASE_URL}/posts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    title: 'Quick Knowledge Share',
                    content,
                    post_type: 'text',
                    tags: []
                })
            });
        }

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Unable to post quick share.', 'error');
            return;
        }

        document.getElementById('quickPostContent').value = '';
        document.getElementById('quickPostFile').value = '';
        document.getElementById('fileStatus').textContent = 'Attach Media';
        showToast('Knowledge shared successfully!', 'success');
        loadPosts();
    } catch (error) {
        console.error('Quick post failed', error);
        showToast('Network error. Is the backend running?', 'error');
    } finally {
        showLoading(false);
    }
}

function updateFileStatus() {
    const files = Array.from(document.getElementById('quickPostFile').files || []);
    const status = document.getElementById('fileStatus');
    if (files.length > 0) {
        status.textContent = `${files.length} file${files.length > 1 ? 's' : ''} selected`;
        status.style.color = '#4caf50';
    } else {
        status.textContent = 'Attach Media';
        status.style.color = '';
    }
}

async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        showFeed();
        return;
    }

    hideAllPages();
    document.getElementById('feedPage').style.display = 'block';
    updateActiveNavLink('feedLink');

    try {
        showLoading(true);

        const [postsResponse, usersResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/posts/search?q=${encodeURIComponent(query)}`),
            fetch(`${API_BASE_URL}/users?q=${encodeURIComponent(query)}`)
        ]);

        if (!postsResponse.ok) {
            showToast('Post search failed. Please try again.', 'error');
            return;
        }
        if (!usersResponse.ok) {
            showToast('User search failed. Please try again.', 'error');
            return;
        }

        const posts = await postsResponse.json();
        const users = await usersResponse.json();
        renderSearchResults(posts, users, query);
    } catch (error) {
        console.error('Search failed', error);
        showToast('Unable to search now.', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadPosts() {
    try {
        const response = await fetch(`${API_BASE_URL}/posts/`);
        if (!response.ok) {
            document.getElementById('postsContainer').innerHTML = '<p class="empty-state">Unable to load posts at the moment.</p>';
            return;
        }

        const posts = await response.json();
        renderPosts(posts);
    } catch (error) {
        console.error('Failed to load posts', error);
        document.getElementById('postsContainer').innerHTML = '<p class="empty-state">Unable to load posts. Check your backend.</p>';
    }
}

function renderSearchResults(posts, users, query) {
    const container = document.getElementById('postsContainer');
    const resultsHeader = `Search results for "${query}"`;
    const usersHtml = Array.isArray(users) && users.length > 0
        ? `<div class="search-users">
                <h3>Users</h3>
                ${users.map(user => `
                    <div class="search-user-card card">
                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.username)}&background=8b5cf6&color=fff&size=128" alt="${user.full_name || user.username}" class="search-user-avatar" onerror="this.onerror=null;this.src='${getAvatarFallbackSvg(user.full_name || user.username)}';" />
                        <div>
                            <strong onclick="showUserProfile('${user.id}')" style="cursor: pointer; color: var(--primary-color);">${user.full_name || user.username}</strong>
                            <span class="user-handle">@${user.username}</span>
                            <p>${user.reliability_score?.toFixed(1) ?? 0}% reliable</p>
                        </div>
                        <button class="btn btn-outline btn-small" onclick="showUserProfile('${user.id}')">View</button>
                        ${currentUser && user.id !== currentUser.id && getAuthToken() ? `<button class="btn btn-connect btn-small" onclick="sendConnectionRequest('${user.id}')"><i class="fas fa-link"></i> Connect</button>` : ''}
                    </div>
                `).join('')}
            </div>`
        : '<div class="search-users"><h3>Users</h3><p>No matching users found.</p></div>';

    const postsHtml = Array.isArray(posts) && posts.length > 0
        ? posts.map(post => {
            const date = post.created_at ? new Date(post.created_at).toLocaleString() : '';
            const tags = Array.isArray(post.tags) ? post.tags.map(tag => `<span class="post-tag">#${tag}</span>`).join(' ') : '';
            const isOwner = currentUser && post.author_id === currentUser.id;
            const isNotCurrentUser = post.author_id !== (currentUser?.id);
            
            const profilePicUrl = getProfileAvatarUrl(post.profile_picture, post.author_name);
            
            const mediaElement = Array.isArray(post.attachments) && post.attachments.length > 0
                ? post.attachments.map(attachment => {
                    if (attachment.mime_type?.startsWith('video/')) {
                        return `<video controls class="post-media" style="max-width: 100%; margin: 10px 0;"><source src="${attachment.url}" type="${attachment.mime_type}"></video>`;
                    }
                    if (attachment.mime_type?.startsWith('image/')) {
                        return `<img src="${attachment.url}" class="post-media" alt="Post media" style="max-width: 100%; margin: 10px 0; border-radius: 8px;">`;
                    }
                    return `<a href="${attachment.url}" target="_blank" class="file-link" style="display: inline-block; padding: 8px 12px; background: #f0f0f0; border-radius: 4px; text-decoration: none; margin: 10px 0;">📎 View Attachment</a>`;
                }).join('')
                : '';

            return `
                <div class="post-card card">
                    <div class="post-header-with-avatar">
                        <img src="${profilePicUrl}" alt="${post.author_name || 'User'}" class="post-avatar-pic" onerror="this.onerror=null;this.src='${getAvatarFallbackSvg(post.author_name)}';" />
                        <div class="post-header-info">
                            <div class="post-author-section">
                                <strong class="post-author-name" onclick="showUserProfile('${post.author_id}')" style="cursor: pointer; color: var(--primary-color);">${post.author_name || 'User'}</strong>
                                <span class="post-meta">${post.post_type || 'Text'} • ${date}</span>
                            </div>
                            <div class="post-header-right">
                                <div class="rating">Reliability <span class="reliability-score">${post.reliability_score?.toFixed(1) ?? 'N/A'}%</span></div>
                                ${isNotCurrentUser && getAuthToken() ? `<button class="btn btn-connect btn-small" onclick="sendConnectionRequest('${post.author_id}')"><i class="fas fa-link"></i> Connect</button>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="post-body">
                        <h3 class="post-title">${post.title || 'Knowledge share'}</h3>
                        <p>${post.content || ''}</p>
                        ${mediaElement}
                        ${tags ? `<div class="post-tags">${tags}</div>` : ''}
                    </div>
                    <div class="post-actions">
                        <button class="post-action-btn" onclick="handleLikePost('${post.id}')">👍 Like (${post.likes_count || 0})</button>
                        <button class="post-action-btn" onclick="toggleComments('${post.id}')">💬 Comments (${post.comments_count || 0})</button>
                        ${isOwner ? `<button class="post-action-btn delete" onclick="handleDeletePost('${post.id}')">🗑️ Delete</button>` : ''}
                    </div>
                    <div class="post-comments" id="commentsSection-${post.id}" style="display: none;">
                        <div class="comment-list" id="commentList-${post.id}"></div>
                        ${getAuthToken() ? `
                            <div class="comment-form">
                                <textarea id="commentInput-${post.id}" class="comment-input" rows="3" placeholder="Write a comment..."></textarea>
                                <button class="btn btn-primary btn-small" onclick="submitComment('${post.id}')">Post Comment</button>
                            </div>
                        ` : `
                            <p class="comment-login-note">Please log in to leave a comment.</p>
                        `}
                    </div>
                </div>
            `;
        }).join('')
        : '<p class="empty-state">No matching posts found.</p>';

    container.innerHTML = `
        <div class="search-results-header">
            <h2>${resultsHeader}</h2>
        </div>
        ${usersHtml}
        <div class="search-posts">
            <h3>Posts</h3>
            ${postsHtml}
        </div>
    `;
}

function renderPosts(posts) {
    const container = document.getElementById('postsContainer');
    if (!Array.isArray(posts) || posts.length === 0) {
        container.innerHTML = '<p class="empty-state">No posts found. Create the first knowledge share.</p>';
        return;
    }

    container.innerHTML = posts
        .map(post => {
            const date = post.created_at ? new Date(post.created_at).toLocaleString() : '';
            const tags = Array.isArray(post.tags) ? post.tags.map(tag => `<span class="post-tag">#${tag}</span>`).join(' ') : '';
            const isOwner = currentUser && post.author_id === currentUser.id;
            const isNotCurrentUser = post.author_id !== (currentUser?.id);
            
            // Generate profile picture using author_name
            const authorInitials = (post.author_name || 'U').charAt(0).toUpperCase();
            const profilePicUrl = getProfileAvatarUrl(post.profile_picture, post.author_name);

            let mediaElement = '';
            if (Array.isArray(post.attachments) && post.attachments.length > 0) {
                mediaElement = post.attachments.map(attachment => {
                    if (attachment.mime_type?.startsWith('video/')) {
                        return `<video controls class="post-media" style="max-width: 100%; margin: 10px 0;"><source src="${attachment.url}" type="${attachment.mime_type}"></video>`;
                    }
                    if (attachment.mime_type?.startsWith('image/')) {
                        return `<img src="${attachment.url}" class="post-media" alt="Post media" style="max-width: 100%; margin: 10px 0; border-radius: 8px;">`;
                    }
                    return `<a href="${attachment.url}" target="_blank" class="file-link" style="display: inline-block; padding: 8px 12px; background: #f0f0f0; border-radius: 4px; text-decoration: none; margin: 10px 0;">📎 View Attachment</a>`;
                }).join('');
            }

            return `
                <div class="post-card card">
                    <div class="post-header-with-avatar">
                        <img src="${profilePicUrl}" alt="${post.author_name || 'User'}" class="post-avatar-pic" onerror="this.onerror=null;this.src='${getAvatarFallbackSvg(post.author_name)}';" />
                        <div class="post-header-info">
                            <div class="post-author-section">
                                <strong class="post-author-name" onclick="showUserProfile('${post.author_id}')" style="cursor: pointer; color: var(--primary-color);">${post.author_name || 'User'}</strong>
                                <span class="post-meta">${post.post_type || 'Text'} • ${date}</span>
                            </div>
                            <div class="post-header-right">
                                <div class="rating">Reliability <span class="reliability-score">${post.reliability_score?.toFixed(1) ?? 'N/A'}%</span></div>
                                <button class="btn btn-outline btn-small" onclick="showUserProfile('${post.author_id}')">View posts</button>
                                ${isNotCurrentUser && getAuthToken() ? `<button class="btn btn-connect btn-small" onclick="sendConnectionRequest('${post.author_id}')"><i class="fas fa-link"></i> Connect</button>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="post-body">
                        <h3 class="post-title">${post.title || 'Knowledge share'}</h3>
                        <p>${post.content || ''}</p>
                        ${mediaElement}
                        ${tags ? `<div class="post-tags">${tags}</div>` : ''}
                    </div>
                    <div class="post-actions">
                        <button class="post-action-btn" onclick="handleLikePost('${post.id}')">👍 Like (${post.likes_count || 0})</button>
                        <button class="post-action-btn" onclick="toggleComments('${post.id}')">💬 Comments (${post.comments_count || 0})</button>
                        ${isOwner ? `<button class="post-action-btn delete" onclick="handleDeletePost('${post.id}')">🗑️ Delete</button>` : ''}
                    </div>
                    <div class="post-comments" id="commentsSection-${post.id}" style="display: none;">
                        <div class="comment-list" id="commentList-${post.id}"></div>
                        ${getAuthToken() ? `
                            <div class="comment-form">
                                <textarea id="commentInput-${post.id}" class="comment-input" rows="3" placeholder="Write a comment..."></textarea>
                                <button class="btn btn-primary btn-small" onclick="submitComment('${post.id}')">Post Comment</button>
                            </div>
                        ` : `
                            <p class="comment-login-note">Please log in to leave a comment.</p>
                        `}
                    </div>
                </div>
            `;
        })
        .join('');
}

async function handleLikePost(postId) {
    if (!getAuthToken()) {
        showToast('Please log in to like posts.', 'warning');
        showLogin();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${getAuthToken()}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Unable to like post.', 'error');
            return;
        }

        loadPosts();
    } catch (error) {
        console.error('Like post error', error);
        showToast('Unable to like post now.', 'error');
    }
}

async function handleDeletePost(postId) {
    if (!getAuthToken()) {
        showToast('Please log in to delete posts.', 'warning');
        showLogin();
        return;
    }

    if (!confirm('Are you sure you want to delete this post?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}`, {
            method: 'DELETE',
            headers: {
                Authorization: `Bearer ${getAuthToken()}`
            }
        });

        if (response.status === 204) {
            showToast('Post deleted successfully.', 'success');
            loadPosts();
            return;
        }

        const error = await response.json();
        showToast(error.detail || 'Unable to delete post.', 'error');
    } catch (error) {
        console.error('Delete post error', error);
        showToast('Unable to delete post now.', 'error');
    }
}

function toggleComments(postId) {
    const section = document.getElementById(`commentsSection-${postId}`);
    if (!section) return;

    const isHidden = section.style.display === 'none';
    section.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
        loadComments(postId);
    }
}

async function loadComments(postId) {
    const list = document.getElementById(`commentList-${postId}`);
    if (!list) return;

    list.innerHTML = '<p>Loading comments...</p>';
    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments`);
        if (!response.ok) {
            list.innerHTML = '<p class="comment-error">Unable to load comments.</p>';
            return;
        }

        const comments = await response.json();
        if (!Array.isArray(comments) || comments.length === 0) {
            list.innerHTML = '<p class="comment-empty">No comments yet. Be the first to reply.</p>';
            return;
        }

        list.innerHTML = comments.map(comment => `
            <div class="comment-card">
                <div class="comment-author"><strong>${comment.author_name}</strong> · ${new Date(comment.created_at).toLocaleString()}</div>
                <p class="comment-content">${comment.content}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Load comments failed', error);
        list.innerHTML = '<p class="comment-error">Unable to load comments.</p>';
    }
}

async function submitComment(postId) {
    const input = document.getElementById(`commentInput-${postId}`);
    if (!input) return;

    const content = input.value.trim();
    if (!content) {
        showToast('Please write a comment before posting.', 'error');
        return;
    }

    if (!getAuthToken()) {
        showToast('Please log in to comment.', 'warning');
        showLogin();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ content })
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Could not post comment.', 'error');
            return;
        }

        input.value = '';
        loadComments(postId);
        loadPosts();
    } catch (error) {
        console.error('Submit comment failed', error);
        showToast('Unable to post comment.', 'error');
    }
}

function renderProfile() {
    const profilePage = document.getElementById('profilePage');
    const userToShow = profileViewUser || currentUser;

    if (!userToShow) {
        profilePage.innerHTML = '<div class="container"><h2>Profile</h2><p>Please log in to view your profile.</p></div>';
        return;
    }

    const isOwnProfile = profileViewUser === null;
    const connectionButton = profileViewUser && currentUser && profileViewUser.id !== currentUser.id
        ? `<div class="profile-action-buttons"><button class="btn btn-primary btn-full" onclick="sendConnectionRequest('${profileViewUser.id}')">Connect</button><button class="btn btn-secondary btn-full" onclick="messageUser('${profileViewUser.id}','${profileViewUser.full_name || profileViewUser.username}')"><i class="fas fa-comment"></i> Message</button></div>`
        : isOwnProfile
            ? `<button class="btn btn-primary btn-full" onclick="logout()">Logout</button>`
            : '';

    const connectionCount = ((userToShow.followers_count || 0) + (userToShow.following_count || 0));

    const profileImage = userToShow.profile_picture || 'https://picsum.photos/seed/user/120/120.jpg';
    const postsTitle = isOwnProfile ? 'My Posts' : `${userToShow.full_name || userToShow.username}'s Posts`;

    profilePage.innerHTML = `
        <div class="container">
            <div class="profile-grid">
                <div class="card profile-card">
                    <div class="profile-avatar">
                        <img src="${profileImage}" alt="Profile picture" />
                    </div>
                    <h2>${userToShow.full_name || userToShow.username}</h2>
                    <p><strong>Username:</strong> ${userToShow.username}</p>
                    <p><strong>Email:</strong> ${userToShow.email}</p>
                    <p><strong>Reliability Score:</strong> ${userToShow.reliability_score?.toFixed(1) ?? 0}%</p>
                    <p><strong>Posts:</strong> ${userToShow.posts_count ?? 0}</p>
                    <p><strong>Connections:</strong> ${connectionCount}</p>
                    <p><strong>Badges:</strong> ${(userToShow.badges || []).join(', ') || 'None'}</p>
                    ${connectionButton}
                </div>
                <div class="card profile-card">
                    <h3>About</h3>
                    ${isOwnProfile ? `
                        <div class="profile-bio-section">
                            <textarea id="profileBioInput" rows="4" placeholder="Tell people about yourself...">${userToShow.bio || ''}</textarea>
                            <button class="btn btn-primary btn-full" onclick="saveProfileBio()">Save Bio</button>
                        </div>
                    ` : `
                        <p>${userToShow.bio || 'No bio available yet.'}</p>
                    `}
                    ${isOwnProfile ? `
                        <div class="profile-upload-section">
                            <h4>Upload Profile Picture</h4>
                            <input type="file" id="profilePictureFile" accept="image/*" />
                            <button class="btn btn-primary btn-full" onclick="uploadProfilePicture()">Upload Picture</button>
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="card profile-card">
                <div class="profile-posts-header">
                    <h3>${postsTitle}</h3>
                </div>
                <div id="profilePostsSection" class="profile-posts-list">
                    <p class="empty-state">Loading posts...</p>
                </div>
            </div>
        </div>
    `;

    if (userToShow.id) {
        loadUserPosts(userToShow.id);
    }
}

async function loadUserPosts(userId) {
    const section = document.getElementById('profilePostsSection');
    if (!section) return;
    section.innerHTML = '<p class="empty-state">Loading posts...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/posts/user/${userId}`);
        if (!response.ok) {
            section.innerHTML = '<p class="empty-state">Unable to load posts.</p>';
            return;
        }

        const posts = await response.json();
        renderProfilePosts(posts);
    } catch (error) {
        console.error('Failed to load user posts', error);
        section.innerHTML = '<p class="empty-state">Unable to load posts. Check your connection.</p>';
    }
}

function renderProfilePosts(posts) {
    const section = document.getElementById('profilePostsSection');
    if (!section) return;

    if (!Array.isArray(posts) || posts.length === 0) {
        section.innerHTML = '<p class="empty-state">This user has not shared any posts yet.</p>';
        return;
    }

    section.innerHTML = posts.map(post => {
        const date = post.created_at ? new Date(post.created_at).toLocaleString() : '';
        const tags = Array.isArray(post.tags) ? post.tags.map(tag => `<span class="post-tag">#${tag}</span>`).join(' ') : '';
        const isOwner = currentUser && post.author_id === currentUser.id;
        const isNotCurrentUser = post.author_id !== (currentUser?.id);
        const profilePicUrl = getProfileAvatarUrl(post.profile_picture, post.author_name);

        const mediaElement = Array.isArray(post.attachments) && post.attachments.length > 0
            ? post.attachments.map(attachment => {
                if (attachment.mime_type?.startsWith('video/')) {
                    return `<video controls class="post-media" style="max-width: 100%; margin: 10px 0;"><source src="${attachment.url}" type="${attachment.mime_type}"></video>`;
                }
                if (attachment.mime_type?.startsWith('image/')) {
                    return `<img src="${attachment.url}" class="post-media" alt="Post media" style="max-width: 100%; margin: 10px 0; border-radius: 8px;">`;
                }
                return `<a href="${attachment.url}" target="_blank" class="file-link" style="display: inline-block; padding: 8px 12px; background: #f0f0f0; border-radius: 4px; text-decoration: none; margin: 10px 0;">📎 View Attachment</a>`;
            }).join('')
            : '';

        return `
            <div class="post-card card">
                <div class="post-header-with-avatar">
                    <img src="${profilePicUrl}" alt="${post.author_name || 'User'}" class="post-avatar-pic" onerror="this.onerror=null;this.src='${getAvatarFallbackSvg(post.author_name)}';" />
                    <div class="post-header-info">
                        <div class="post-author-section">
                            <strong class="post-author-name" onclick="showUserProfile('${post.author_id}')" style="cursor: pointer; color: var(--primary-color);">${post.author_name || 'User'}</strong>
                            <span class="post-meta">${post.post_type || 'Text'} • ${date}</span>
                        </div>
                        <div class="post-header-right">
                            <div class="rating">Reliability <span class="reliability-score">${post.reliability_score?.toFixed(1) ?? 'N/A'}%</span></div>
                            ${isNotCurrentUser && getAuthToken() ? `<button class="btn btn-connect btn-small" onclick="sendConnectionRequest('${post.author_id}')"><i class="fas fa-link"></i> Connect</button>` : ''}
                        </div>
                    </div>
                </div>
                <div class="post-body">
                    <h3 class="post-title">${post.title || 'Knowledge share'}</h3>
                    <p>${post.content || ''}</p>
                    ${mediaElement}
                    ${tags ? `<div class="post-tags">${tags}</div>` : ''}
                </div>
                <div class="post-actions">
                    <button class="post-action-btn" onclick="handleLikePost('${post.id}')">👍 Like (${post.likes_count || 0})</button>
                    <button class="post-action-btn" onclick="toggleComments('${post.id}')">💬 Comments (${post.comments_count || 0})</button>
                    ${isOwner ? `<button class="post-action-btn delete" onclick="handleDeletePost('${post.id}')">🗑️ Delete</button>` : ''}
                </div>
                <div class="post-comments" id="commentsSection-${post.id}" style="display: none;">
                    <div class="comment-list" id="commentList-${post.id}"></div>
                    ${getAuthToken() ? `
                        <div class="comment-form">
                            <textarea id="commentInput-${post.id}" class="comment-input" rows="3" placeholder="Write a comment..."></textarea>
                            <button class="btn btn-primary btn-small" onclick="submitComment('${post.id}')">Post Comment</button>
                        </div>
                    ` : `
                        <p class="comment-login-note">Please log in to leave a comment.</p>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

async function fetchUserProfileById(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch user profile', error);
        return null;
    }
}

async function uploadProfilePicture() {
    const fileInput = document.getElementById('profilePictureFile');
    if (!fileInput || fileInput.files.length === 0) {
        showToast('Please select an image to upload.', 'error');
        return;
    }

    const file = fileInput.files[0];
    if (!file.type.startsWith('image/')) {
        showToast('Profile picture must be an image file.', 'error');
        return;
    }

    if (!getAuthToken()) {
        showToast('Please log in first.', 'warning');
        showLogin();
        return;
    }

    try {
        showLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/users/me/profile-picture`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${getAuthToken()}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Could not upload profile picture.', 'error');
            return;
        }

        const updatedUser = await response.json();
        saveCurrentUser(updatedUser);
        updateAuthUI(true);
        renderProfile();
        showToast('Profile picture uploaded successfully!', 'success');
    } catch (error) {
        console.error('Upload profile picture failed', error);
        showToast('Unable to upload profile picture.', 'error');
    } finally {
        showLoading(false);
    }
}

async function saveProfileBio() {
    const bioInput = document.getElementById('profileBioInput');
    if (!bioInput) {
        return;
    }

    const bioText = bioInput.value.trim();
    if (!getAuthToken()) {
        showToast('Please log in first.', 'warning');
        showLogin();
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ bio: bioText })
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Could not update bio.', 'error');
            return;
        }

        const updatedUser = await response.json();
        saveCurrentUser(updatedUser);
        updateAuthUI(true);
        renderProfile();
        showToast('Bio updated successfully!', 'success');
    } catch (error) {
        console.error('Save bio failed', error);
        showToast('Unable to save bio.', 'error');
    } finally {
        showLoading(false);
    }
}

async function renderConnections() {
    const connectionsPage = document.getElementById('connectionsPage');
    if (!getAuthToken()) {
        connectionsPage.innerHTML = '<div class="container"><h2>My Connections</h2><p>Please log in to view your connections and pending requests.</p></div>';
        return;
    }

    try {
        showLoading(true);
        const [connectionsResponse, pendingResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/connections/my-connections`, {
                headers: { Authorization: `Bearer ${getAuthToken()}` }
            }),
            fetch(`${API_BASE_URL}/connections/pending`, {
                headers: { Authorization: `Bearer ${getAuthToken()}` }
            })
        ]);

        if (!connectionsResponse.ok || !pendingResponse.ok) {
            connectionsPage.innerHTML = '<div class="container"><h2>My Connections</h2><p>Unable to load your connections right now.</p></div>';
            return;
        }

        const connections = await connectionsResponse.json();
        const pending = await pendingResponse.json();

        const connectedUsers = await Promise.all(connections.map(async conn => {
            const otherUserId = conn.requester_id === currentUser.id ? conn.requested_id : conn.requester_id;
            const otherUser = await fetchUserProfileById(otherUserId);
            return { connection: conn, otherUser };
        }));

        const pendingUsers = await Promise.all(pending.map(async conn => {
            const requesterUser = await fetchUserProfileById(conn.requester_id);
            return { connection: conn, requesterUser };
        }));

        connectionsPage.innerHTML = `
            <div class="container">
                <div class="card">
                    <h2>My Connections</h2>
                    ${connectedUsers.length ? connectedUsers.map(({ connection, otherUser }) => `
                            <div class="connection-card">
                                <div>
                                    <p><strong>${otherUser ? otherUser.full_name : 'User'}</strong> <span class="user-handle">@${otherUser ? otherUser.username : connection.requester_id}</span></p>
                                    <p>Status: ${connection.status}</p>
                                </div>
                                <button class="btn btn-outline btn-small" onclick="showUserProfile('${otherUser ? otherUser.id : (connection.requester_id === currentUser.id ? connection.requested_id : connection.requester_id)}')">View</button>
                            </div>
                        `).join('') : '<p>No connections yet. Search users to connect.</p>'}
                </div>
                <div class="card">
                    <h2>Pending Requests</h2>
                    ${pendingUsers.length ? pendingUsers.map(({ connection, requesterUser }) => `
                            <div class="connection-card">
                                <div>
                                    <p><strong>${requesterUser ? requesterUser.full_name : 'User'}</strong> <span class="user-handle">@${requesterUser ? requesterUser.username : connection.requester_id}</span></p>
                                    <p>Status: ${connection.status}</p>
                                </div>
                                <div class="connection-actions">
                                    <button class="btn btn-primary btn-small" onclick="handleAcceptConnection('${connection.id}')">Accept</button>
                                    <button class="btn btn-outline btn-small" onclick="handleRejectConnection('${connection.id}')">Reject</button>
                                </div>
                            </div>
                        `).join('') : '<p>No pending requests.</p>'}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Load connections failed', error);
        connectionsPage.innerHTML = '<div class="container"><h2>My Connections</h2><p>Unable to load connections due to network error.</p></div>';
    } finally {
        showLoading(false);
    }
}

async function handleAcceptConnection(connectionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/connections/${connectionId}/accept`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${getAuthToken()}` }
        });
        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Unable to accept connection.', 'error');
            return;
        }
        showToast('Connection accepted.', 'success');
        fetchCurrentUser();
        renderConnections();
    } catch (error) {
        console.error('Accept connection failed', error);
        showToast('Unable to accept connection now.', 'error');
    }
}

async function handleRejectConnection(connectionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/connections/${connectionId}/reject`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${getAuthToken()}` }
        });
        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Unable to reject connection.', 'error');
            return;
        }
        showToast('Connection rejected.', 'success');
        renderConnections();
    } catch (error) {
        console.error('Reject connection failed', error);
        showToast('Unable to reject connection now.', 'error');
    }
}

async function sendConnectionRequest(userId) {
    if (!getAuthToken()) {
        showToast('Please log in to connect with users.', 'warning');
        showLogin();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/connections/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ requested_id: userId })
        });

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Unable to send connection request.', 'error');
            return;
        }

        showToast('Connection request sent.', 'success');
        if (profileViewUser && profileViewUser.id === userId) {
            showUserProfile(userId);
        }
    } catch (error) {
        console.error('Connection request failed', error);
        showToast('Unable to connect now.', 'error');
    }
}

function logout() {
    clearAuthData();
    updateAuthUI(false);
    showToast('You have been logged out.', 'success');
    showHome();
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3500);
}

// Chat functionality
let currentChatUser = null;
let websocket = null;

function initializeChat() {
    initializeChatTheme();
    loadConversations();
    loadSolvedLibrary();
    connectWebSocket();
    const chatSearchInput = document.getElementById('chatUserSearchInput');
    if (chatSearchInput && !chatSearchInput.dataset.chatListener) {
        chatSearchInput.dataset.chatListener = '1';
        chatSearchInput.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                searchChatUsers();
            }
        });
    }
}

function connectWebSocket() {
    const token = getAuthToken();
    if (!token || !currentUser) return;
    if (websocket && websocket.readyState === WebSocket.OPEN) return;

    const userId = currentUser.id;
    websocket = new WebSocket(`ws://127.0.0.1:8000/api/chat/ws/${userId}`);

    websocket.onopen = () => {
        console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message' || data.type === 'message_sent') {
            handleIncomingMessage(data.message);
        }
    };

    websocket.onclose = () => {
        console.log('WebSocket disconnected');
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function loadConversations() {
    fetch(`${API_BASE_URL}/chat/conversations`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(conversations => {
        renderConversations(conversations);
    })
    .catch(error => {
        console.error('Error loading conversations:', error);
    });
}

function renderConversations(conversations) {
    const container = document.getElementById('conversationsList');
    container.innerHTML = '';

    if (conversations.length === 0) {
        container.innerHTML = '<p>No conversations yet. Start chatting with someone!</p>';
        return;
    }

    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
item.onclick = () => openConversation(conv.user_id, conv.username, item);

        const unreadBadge = conv.unread_count > 0 ? `<span class="unread-badge">${conv.unread_count}</span>` : '';

        item.innerHTML = `
            <div class="conversation-info">
                <strong>${conv.full_name || conv.username}</strong>
                ${unreadBadge}
            </div>
        `;

        container.appendChild(item);
    });
}

function openConversation(userId, username, element) {
    currentChatUser = { id: userId, name: username };

    setChatHeader(username);
    showChatInput(true);
    loadConversation(userId);

    document.querySelectorAll('.conversation-item').forEach(item => item.classList.remove('active'));
    if (element) {
        element.classList.add('active');
    }
}

function loadConversation(userId) {
    fetch(`${API_BASE_URL}/chat/conversation/${userId}`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(messages => {
        renderMessages(messages);
    })
    .catch(error => {
        console.error('Error loading conversation:', error);
    });
}

function renderMessages(messages) {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';

    const threadGroups = {};
    const roots = [];
    const bestAnswerIds = new Set();

    messages.forEach(msg => {
        if (msg.thread_root_id) {
            threadGroups[msg.thread_root_id] = threadGroups[msg.thread_root_id] || [];
            threadGroups[msg.thread_root_id].push(msg);
        } else {
            roots.push(msg);
        }
    });

    roots.forEach(root => {
        if (root.best_answer_id) {
            bestAnswerIds.add(root.best_answer_id);
        }
    });

    const renderMessageCard = (msg, nested = false) => {
        const messageDiv = document.createElement('div');
        const isSent = msg.sender_id === currentUser.id;
        let messageClass = `message ${isSent ? 'sent' : 'received'}`;
        if (msg.is_challenge) messageClass += ' challenge';
        if (nested) messageClass += ' thread-reply';
        if (bestAnswerIds.has(msg.id)) messageClass += ' best-answer';
        messageDiv.className = messageClass;

        const title = msg.is_challenge
            ? `<div class="sender">${msg.sender_name} <span class="challenge-badge">Challenge</span> <span class="status-label">${msg.challenge_status || 'open'}</span></div>`
            : `<div class="sender">${msg.sender_name}</div>`;

        const contentHtml = msg.message_type === 'code'
            ? `<pre class="code-block">${escapeHtml(msg.content)}</pre><div class="code-meta">${msg.metadata?.language || 'code snippet'}</div>`
            : msg.message_type === 'poll'
                ? renderPollHtml(msg)
                : `<div class="content">${escapeHtml(msg.content)}</div>`;

        const timestampHtml = `<div class="timestamp">${new Date(msg.created_at).toLocaleString()}${msg.edited ? ' • edited' : ''}</div>`;
        messageDiv.innerHTML = `${title}${contentHtml}${timestampHtml}`;

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';

        if (currentUser && (msg.sender_id === currentUser.id || currentUser.is_admin)) {
            const exportBtn = document.createElement('button');
            exportBtn.className = 'message-action-btn';
            exportBtn.textContent = 'Export';
            exportBtn.addEventListener('click', () => exportMessageToKB(msg.id));
            actionsDiv.appendChild(exportBtn);
        }

        if (msg.sender_id === currentUser.id) {
            const editBtn = document.createElement('button');
            editBtn.className = 'message-action-btn';
            editBtn.textContent = 'Edit';
            editBtn.addEventListener('click', () => editMessage(msg.id, msg.content));
            actionsDiv.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'message-action-btn danger';
            deleteBtn.textContent = 'Delete';
            deleteBtn.addEventListener('click', () => deleteMessageById(msg.id));
            actionsDiv.appendChild(deleteBtn);
        }

        if (msg.is_challenge && !nested) {
            const replyBtn = document.createElement('button');
            replyBtn.className = 'message-action-btn';
            replyBtn.textContent = 'Reply in thread';
            replyBtn.addEventListener('click', () => replyInThread(msg.id));
            actionsDiv.appendChild(replyBtn);
        }

        if (msg.thread_root_id && currentUser) {
            const parentRoot = roots.find(root => root.id === msg.thread_root_id);
            if (parentRoot && (parentRoot.sender_id === currentUser.id || currentUser.is_admin)) {
                const bestBtn = document.createElement('button');
                bestBtn.className = 'message-action-btn success';
                bestBtn.textContent = 'Mark Best Answer';
                bestBtn.addEventListener('click', () => markBestAnswer(msg.thread_root_id, msg.id));
                actionsDiv.appendChild(bestBtn);
            }
        }

        messageDiv.appendChild(actionsDiv);
        container.appendChild(messageDiv);
    };

    roots.forEach(root => {
        renderMessageCard(root, false);
        if (threadGroups[root.id]) {
            threadGroups[root.id].forEach(reply => renderMessageCard(reply, true));
        }
    });

    container.scrollTop = container.scrollHeight;
}

function renderPollHtml(msg) {
    const question = escapeHtml(msg.content);
    const options = Array.isArray(msg.metadata?.options) ? msg.metadata.options : [];
    const listItems = options.map(option => `<li>${escapeHtml(option)}</li>`).join('');
    return `<div class="poll-block"><strong>${question}</strong><ul>${listItems}</ul></div>`;
}

function escapeHtml(value) {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();

    if (!content || !currentChatUser) return;
    sendStructuredMessage('text', content);
    input.value = '';
}

function sendStructuredMessage(messageType, content, metadata = {}) {
    if (!content || !currentChatUser) return;

    const messageData = {
        receiver_id: currentChatUser.id,
        content,
        message_type: messageType,
        metadata,
        is_challenge: challengeMode,
        thread_root_id: currentThreadRoot || undefined
    };

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(messageData));
        if (messageType === 'text') {
            const input = document.getElementById('messageInput');
            if (input) input.value = '';
        }
        if (challengeMode) {
            challengeMode = false;
            updateChallengeToggle();
        }
        if (currentThreadRoot) {
            currentThreadRoot = null;
            renderThreadState();
        }
    } else {
        showToast('Connection lost. Please refresh the page.', 'error');
    }
}

function toggleChallengeMode() {
    challengeMode = !challengeMode;
    if (challengeMode) {
        currentThreadRoot = null;
    }
    updateChallengeToggle();
    renderThreadState();
}

function updateChallengeToggle() {
    const btn = document.getElementById('challengeToggleBtn');
    if (!btn) return;
    if (challengeMode) {
        btn.classList.add('active');
        btn.textContent = 'Challenge Active';
    } else {
        btn.classList.remove('active');
        btn.textContent = 'Mark as Challenge';
    }
}

function renderThreadState() {
    const banner = document.getElementById('chatSuggestionBanner');
    if (!banner) return;

    if (currentThreadRoot) {
        banner.innerHTML = `<span class="thread-state">Replying in challenge thread</span>`;
        return;
    }

    if (challengeMode) {
        banner.innerHTML = `<span class="thread-state">Challenge mode is active. Your next message will start a solution thread.</span>`;
        return;
    }

    banner.innerHTML = lastKnowledgeSuggestion || '';
}

function insertCodeBlock() {
    const code = prompt('Paste your code snippet:');
    if (!code || !currentChatUser) return;
    const language = prompt('Language (optional)', 'javascript') || 'text';
    sendStructuredMessage('code', code, { language });
}

function createPoll() {
    const question = prompt('Poll question:');
    if (!question || !currentChatUser) return;
    const options = prompt('Enter poll options separated by a semicolon (;)');
    if (!options) return;
    const choices = options.split(';').map(option => option.trim()).filter(Boolean);
    if (choices.length < 2) {
        showToast('Please add at least two poll options.', 'warning');
        return;
    }
    sendStructuredMessage('poll', question, { options: choices, votes: {} });
}

function getKnowledgeSuggestion(query) {
    if (!query || query.length < 3) {
        clearSuggestion();
        return;
    }

    fetch(`${API_BASE_URL}/chat/knowledge-suggestions?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(posts => {
            if (!Array.isArray(posts) || posts.length === 0) {
                clearSuggestion();
                return;
            }
            const post = posts[0];
            lastKnowledgeSuggestion = `<span class="suggestion-text">Hey, this looks similar to <strong>${post.title}</strong>. <a href="#" onclick="openPostSuggestion('${post.id}')">View article</a> before posting.</span>`;
            renderThreadState();
        })
        .catch(() => {
            clearSuggestion();
        });
}

function openPostSuggestion(postId) {
    showToast('Feature not available yet. Search the knowledge base for similar articles.', 'info');
    return false;
}

function clearSuggestion() {
    lastKnowledgeSuggestion = '';
    const banner = document.getElementById('chatSuggestionBanner');
    if (banner) {
        banner.innerHTML = '';
    }
}

function loadSolvedLibrary() {
    fetch(`${API_BASE_URL}/chat/challenges/solved`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => response.json())
    .then(solved => renderSolvedChallenges(solved))
    .catch(error => {
        console.error('Unable to load solved library:', error);
        const container = document.getElementById('solvedChallengesList');
        if (container) {
            container.innerHTML = '<p class="empty-state">Unable to load solved threads.</p>';
        }
    });
}

function renderSolvedChallenges(challenges) {
    const container = document.getElementById('solvedChallengesList');
    if (!container) return;

    if (!Array.isArray(challenges) || challenges.length === 0) {
        container.innerHTML = '<p class="empty-state">No solved challenge threads yet.</p>';
        return;
    }

    container.innerHTML = challenges.map(challenge => {
        const otherId = currentUser && challenge.sender_id === currentUser.id ? challenge.receiver_id : challenge.sender_id;
        const otherName = currentUser && challenge.sender_id === currentUser.id ? challenge.receiver_name : challenge.sender_name;
        const title = challenge.content.length > 60 ? `${challenge.content.slice(0, 58)}…` : challenge.content;
        return `<div class="solved-card" onclick="openSolvedThread('${challenge.id}', '${otherId}', '${otherName}')">
            <strong>${title}</strong>
            <span>Solved by ${challenge.sender_name}</span>
        </div>`;
    }).join('');
}

function openSolvedThread(challengeId, otherUserId, otherName) {
    if (!otherUserId) return;
    messageUser(otherUserId, otherName);
    showToast('Opened solved thread conversation.', 'success');
}

function exportMessageToKB(messageId) {
    const title = prompt('Title for the exported article (optional):');
    if (!messageId) return;

    fetch(`${API_BASE_URL}/chat/message/${messageId}/export`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title })
    })
    .then(response => response.json())
    .then(result => {
        showToast('Message exported to knowledge base.', 'success');
        loadSolvedLibrary();
    })
    .catch(error => {
        console.error('Export failed:', error);
        showToast('Unable to export message to knowledge base.', 'error');
    });
}

function markBestAnswer(challengeId, answerId) {
    fetch(`${API_BASE_URL}/chat/challenge/${challengeId}/best-answer/${answerId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Unable to mark best answer');
        return response.json();
    })
    .then(() => {
        if (currentChatUser) {
            loadConversation(currentChatUser.id);
        }
        loadSolvedLibrary();
        showToast('Best answer marked.', 'success');
    })
    .catch(error => {
        console.error('Best answer marking failed:', error);
        showToast('Unable to mark best answer.', 'error');
    });
}

function replyInThread(rootId) {
    currentThreadRoot = rootId;
    challengeMode = false;
    updateChallengeToggle();
    renderThreadState();
    showToast('Replying in the current challenge thread.', 'success');
}

function editMessage(messageId, currentContent) {
    const newContent = prompt('Edit your message', currentContent);
    if (newContent === null || newContent.trim() === '' || newContent.trim() === currentContent.trim()) {
        return;
    }

    fetch(`${API_BASE_URL}/chat/message/${messageId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newContent.trim() })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Unable to update message');
        }
        return response.json();
    })
    .then(() => {
        if (currentChatUser) {
            loadConversation(currentChatUser.id);
        }
        loadConversations();
        showToast('Message updated.', 'success');
    })
    .catch(error => {
        console.error('Edit message failed:', error);
        showToast('Unable to update message.', 'error');
    });
}

function deleteMessageById(messageId) {
    if (!confirm('Delete this message?')) {
        return;
    }

    fetch(`${API_BASE_URL}/chat/message/${messageId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Unable to delete message');
        }
        return response.json();
    })
    .then(() => {
        if (currentChatUser) {
            loadConversation(currentChatUser.id);
        }
        loadConversations();
        showToast('Message deleted.', 'success');
    })
    .catch(error => {
        console.error('Delete message failed:', error);
        showToast('Unable to delete message.', 'error');
    });
}

function handleIncomingMessage(message) {
    if (currentChatUser && (message.sender_id === currentChatUser.id || message.receiver_id === currentChatUser.id)) {
        loadConversation(currentChatUser.id);
    }

    loadConversations();
}

// Handle Enter key in message input
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendMessage();
            }
        });

        messageInput.addEventListener('input', () => {
            const value = messageInput.value.trim();
            if (value.length < 5) {
                clearSuggestion();
                return;
            }
            if (knowledgeSuggestionTimer) {
                clearTimeout(knowledgeSuggestionTimer);
            }
            knowledgeSuggestionTimer = setTimeout(() => {
                getKnowledgeSuggestion(value);
            }, 600);
        });
    }
});
