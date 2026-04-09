// Admin Panel JavaScript
const API_BASE_URL = "http://127.0.0.1:8000/api";
const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';
let currentUser = null;
let currentTab = "dashboard";
let allUsers = [];
let suspendedUsers = [];
let currentPage = 0;
const USERS_PER_PAGE = 10;
let searchTimeout;
let pendingAction = null;

// Check authentication
window.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const userData = localStorage.getItem(AUTH_USER_KEY);
    if (!token || !userData) {
        window.location.href = "index.html";
        return;
    }

    currentUser = JSON.parse(userData);
    verifyAdminAccess();
    loadDashboard();
});

async function verifyAdminAccess() {
    if (!currentUser || !currentUser.is_admin) {
        window.location.href = "index.html";
        return;
    }

    document.getElementById("adminName").textContent = currentUser.full_name || currentUser.username || currentUser.email.split("@")[0];
}

// Tab Navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll(".tab-content").forEach((tab) => {
        tab.classList.remove("active");
    });

    // Remove active class from nav items
    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.remove("active");
    });

    // Show selected tab
    document.getElementById(tabName).classList.add("active");

    // Add active class to matching nav item
    const clickedTab = document.querySelector(`.nav-item[data-tab="${tabName}"]`);
    if (clickedTab) {
        clickedTab.classList.add("active");
    }

    // Update page title
    const titles = {
        dashboard: "Admin Dashboard",
        users: "Manage Users",
        suspended: "Suspended Users",
        moderation: "Moderation & Safety",
    };
    document.getElementById("pageTitle").textContent = titles[tabName];

    currentTab = tabName;

    // Load data based on tab
    if (tabName === "users") {
        loadAllUsers();
    } else if (tabName === "suspended") {
        loadSuspendedUsers();
    }
}

// Dashboard
async function loadDashboard() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            if (response.status === 403) {
                showNotification("You do not have admin access", "error");
                setTimeout(() => (window.location.href = "index.html"), 2000);
            }
            throw new Error("Failed to load dashboard");
        }

        const data = await response.json();

        document.getElementById("totalUsers").textContent = data.total_users;
        document.getElementById("activeUsers").textContent = data.active_users;
        document.getElementById("suspendedUsers").textContent =
            data.suspended_users;
        document.getElementById("adminUsers").textContent = data.admin_users;
    } catch (error) {
        console.error("Error loading dashboard:", error);
        showNotification("Failed to load dashboard statistics", "error");
    }
}

// Load all users
async function loadAllUsers(page = 0) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const skip = page * USERS_PER_PAGE;

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users?skip=${skip}&limit=${USERS_PER_PAGE}`,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            }
        );

        if (!response.ok) throw new Error("Failed to load users");

        const data = await response.json();
        allUsers = data.users;

        renderUsersTable(allUsers);
        renderPagination(page, Math.ceil(data.total / USERS_PER_PAGE));

        currentPage = page;
    } catch (error) {
        console.error("Error loading users:", error);
        showNotification("Failed to load users", "error");
    }
}

// Render users table
function renderUsersTable(users) {
    const tableBody = document.getElementById("usersTableBody");

    if (users.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="no-data">No users found</td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = users
        .map(
            (user) => `
        <tr>
            <td><strong>${escapeHtml(user.username)}</strong></td>
            <td>${escapeHtml(user.email)}</td>
            <td>${escapeHtml(user.full_name)}</td>
            <td>${user.reliability_score.toFixed(1)}</td>
            <td>
                <span class="badge ${user.is_suspended ? "badge-suspended" : "badge-active"}">
                    ${user.is_suspended ? "Suspended" : "Active"}
                </span>
            </td>
            <td>
                <span class="badge ${user.is_admin ? "badge-admin" : ""}">
                    ${user.is_admin ? "Admin" : "User"}
                </span>
            </td>
            <td>
                <div class="action-buttons-inline">
                    <button class="btn-small btn-small-primary" onclick="viewUserDetails('${user.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${
                        user.is_suspended
                            ? `<button class="btn-small btn-small-success" onclick="activateUserAction('${user.id}', '${escapeHtml(user.username)}')">
                        <i class="fas fa-check"></i>
                    </button>`
                            : `<button class="btn-small btn-small-warning" onclick="suspendUserModal('${user.id}', '${escapeHtml(user.username)}')">
                        <i class="fas fa-ban"></i>
                    </button>`
                    }
                    <button class="btn-small ${user.is_admin ? "btn-small-danger" : "btn-small-primary"}" onclick="toggleAdminAction('${user.id}', '${escapeHtml(user.username)}', ${user.is_admin})">
                        <i class="fas fa-${user.is_admin ? "times" : "crown"}"></i>
                    </button>
                    <button class="btn-small btn-small-danger" onclick="deleteUserAction('${user.id}', '${escapeHtml(user.username)}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `
        )
        .join("");
}

// Render pagination
function renderPagination(currentPage, totalPages) {
    const pagination = document.getElementById("usersPagination");

    let html = "";

    // Previous button
    if (currentPage > 0) {
        html += `<button class="pagination-btn" onclick="loadAllUsers(${currentPage - 1})">← Previous</button>`;
    }

    // Page numbers
    for (let i = Math.max(0, currentPage - 2); i < Math.min(currentPage + 3, totalPages); i++) {
        html += `<button class="pagination-btn ${i === currentPage ? "active" : ""}" onclick="loadAllUsers(${i})">${i + 1}</button>`;
    }

    // Next button
    if (currentPage < totalPages - 1) {
        html += `<button class="pagination-btn" onclick="loadAllUsers(${currentPage + 1})">Next →</button>`;
    }

    pagination.innerHTML = html;
}

// Load suspended users
async function loadSuspendedUsers() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(`${API_BASE_URL}/admin/users/suspended`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) throw new Error("Failed to load suspended users");

        suspendedUsers = await response.json();
        renderSuspendedTable(suspendedUsers);
    } catch (error) {
        console.error("Error loading suspended users:", error);
        showNotification("Failed to load suspended users", "error");
    }
}

// Render suspended users table
function renderSuspendedTable(users) {
    const tableBody = document.getElementById("suspendedTableBody");

    if (users.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="no-data">No suspended users</td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = users
        .map(
            (user) => `
        <tr>
            <td><strong>${escapeHtml(user.username)}</strong></td>
            <td>${escapeHtml(user.email)}</td>
            <td>${escapeHtml(user.suspension_reason || "No reason provided")}</td>
            <td>${new Date(user.updated_at).toLocaleDateString()}</td>
            <td>
                <button class="btn-small btn-small-success" onclick="activateUserAction('${user.id}', '${escapeHtml(user.username)}')">
                    <i class="fas fa-check"></i> Activate
                </button>
            </td>
        </tr>
    `
        )
        .join("");
}

// Search users
function debounceSearch() {
    clearTimeout(searchTimeout);
    const query = document.getElementById("userSearchInput").value.trim();

    searchTimeout = setTimeout(() => {
        if (query.length >= 2) {
            searchUsersByQuery(query);
        } else if (query.length === 0) {
            loadAllUsers(0);
        }
    }, 300);
}

async function searchUsersByQuery(query) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/search?query=${encodeURIComponent(query)}&limit=50`,
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            }
        );

        if (!response.ok) throw new Error("Search failed");

        const data = await response.json();
        renderUsersTable(data.users);
        document.getElementById("usersPagination").innerHTML = "";
    } catch (error) {
        console.error("Error searching users:", error);
        showNotification("Search failed", "error");
    }
}

// View user details
async function viewUserDetails(userId) {
    const user = allUsers.find((u) => u.id === userId);
    if (!user) return;

    const content = document.getElementById("userActionContent");
    content.innerHTML = `
        <div style="padding: 20px;">
            <div style="margin-bottom: 20px;">
                <h3>${escapeHtml(user.username)}</h3>
                <p style="color: #666; margin: 5px 0;"><strong>Email:</strong> ${escapeHtml(user.email)}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Full Name:</strong> ${escapeHtml(user.full_name)}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Reliability Score:</strong> ${user.reliability_score.toFixed(1)}/100</p>
                <p style="color: #666; margin: 5px 0;"><strong>Posts:</strong> ${user.posts_count}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Followers:</strong> ${user.followers_count}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Following:</strong> ${user.following_count}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Joined:</strong> ${new Date(user.created_at).toLocaleDateString()}</p>
                <p style="color: #666; margin: 5px 0;"><strong>Status:</strong> 
                    <span class="badge ${user.is_suspended ? "badge-suspended" : "badge-active"}">
                        ${user.is_suspended ? "Suspended" : "Active"}
                    </span>
                </p>
                ${user.is_suspended ? `<p style="color: #f59e0b; margin: 5px 0;"><strong>Suspension Reason:</strong> ${escapeHtml(user.suspension_reason)}</p>` : ""}
            </div>
        </div>
    `;

    openModal("userActionModal");
}

// Suspend user with modal
function suspendUserModal(userId, username) {
    pendingAction = { type: "suspend", userId, username };
    openModal("suspensionModal");
}

function confirmSuspension(event) {
    event.preventDefault();
    const reason = document.getElementById("suspensionReason").value.trim();

    if (!reason) {
        showNotification("Please provide a suspension reason", "error");
        return;
    }

    closeModal("suspensionModal");
    suspendUser(pendingAction.userId, pendingAction.username, reason);
}

async function suspendUser(userId, username, reason) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/${userId}/suspend?reason=${encodeURIComponent(reason)}`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            }
        );

        if (!response.ok) throw new Error("Failed to suspend user");

        showNotification(`User ${username} has been suspended`, "success");
        document.getElementById("suspensionReason").value = "";
        loadAllUsers(currentPage);
        loadSuspendedUsers();
    } catch (error) {
        console.error("Error suspending user:", error);
        showNotification("Failed to suspend user", "error");
    }
}

// Activate user
async function activateUserAction(userId, username) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/${userId}/activate`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            }
        );

        if (!response.ok) throw new Error("Failed to activate user");

        showNotification(`User ${username} has been activated`, "success");
        loadAllUsers(currentPage);
        loadSuspendedUsers();
    } catch (error) {
        console.error("Error activating user:", error);
        showNotification("Failed to activate user", "error");
    }
}

// Toggle admin status
function toggleAdminAction(userId, username, isCurrentlyAdmin) {
    if (isCurrentlyAdmin) {
        showConfirmation(
            "Remove Admin Status",
            `Are you sure you want to remove admin privileges from ${username}?`,
            () => removeAdminStatus(userId, username)
        );
    } else {
        showConfirmation(
            "Promote to Admin",
            `Are you sure you want to promote ${username} to admin? They will have full access to the admin panel.`,
            () => makeAdmin(userId, username)
        );
    }
}

async function makeAdmin(userId, username) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/${userId}/make-admin`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            }
        );

        if (!response.ok) throw new Error("Failed to promote user");

        showNotification(`User ${username} is now an admin`, "success");
        loadAllUsers(currentPage);
    } catch (error) {
        console.error("Error promoting user:", error);
        showNotification("Failed to promote user to admin", "error");
    }
}

async function removeAdminStatus(userId, username) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/${userId}/remove-admin`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            }
        );

        if (!response.ok) throw new Error("Failed to remove admin status");

        showNotification(
            `Admin privileges removed from ${username}`,
            "success"
        );
        loadAllUsers(currentPage);
    } catch (error) {
        console.error("Error removing admin status:", error);
        showNotification("Failed to remove admin status", "error");
    }
}

// Delete user
function deleteUserAction(userId, username) {
    showConfirmation(
        "Delete User",
        `Are you sure you want to permanently delete ${username}? This action cannot be undone.`,
        () => deleteUser(userId, username)
    );
}

async function deleteUser(userId, username) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
        const response = await fetch(
            `${API_BASE_URL}/admin/users/${userId}/delete`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            }
        );

        if (!response.ok) throw new Error("Failed to delete user");

        showNotification(`User ${username} has been deleted`, "success");
        loadAllUsers(currentPage);
    } catch (error) {
        console.error("Error deleting user:", error);
        showNotification("Failed to delete user", "error");
    }
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add("show");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove("show");
}

// Confirmation dialog
function showConfirmation(title, message, callback) {
    document.getElementById("confirmTitle").textContent = title;
    document.getElementById("confirmMessage").textContent = message;
    pendingAction = callback;
    openModal("confirmationModal");
}

function executeConfirmedAction() {
    closeModal("confirmationModal");
    if (typeof pendingAction === "function") {
        pendingAction();
    }
}

// Notification
function showNotification(message, type = "info") {
    const notification = document.getElementById("notification");
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove("show");
    }, 3000);
}

// Utility functions
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Refresh data
function refreshData() {
    loadDashboard();
    if (currentTab === "users") {
        loadAllUsers(currentPage);
    } else if (currentTab === "suspended") {
        loadSuspendedUsers();
    }
    showNotification("Data refreshed", "success");
}

// Navigation
function goHome() {
    window.location.href = "index.html";
}

function logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    window.location.href = "index.html";
}

// Search user modal placeholder
function searchUserModal() {
    document.getElementById("userSearchInput").focus();
}
