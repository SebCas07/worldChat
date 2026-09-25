const state = {
  currentUserId: null,
  activeThread: null,
  activeThreadType: "server",
  appData: {
    current_user: null,
    users: [],
    servers: [],
    dm_threads: [],
    suggestions: [],
  },
};

const elements = {
  registerForm: document.getElementById("register-form"),
  registerName: document.getElementById("register-name"),
  loginForm: document.getElementById("login-form"),
  loginUser: document.getElementById("login-user"),
  logoutButton: document.getElementById("logout-button"),
  createServerForm: document.getElementById("create-server-form"),
  serverName: document.getElementById("server-name"),
  serverDescription: document.getElementById("server-description"),
  joinServerForm: document.getElementById("join-server-form"),
  inviteCode: document.getElementById("invite-code"),
  serverList: document.getElementById("server-list"),
  userList: document.getElementById("user-list"),
  dmList: document.getElementById("dm-list"),
  suggestionForm: document.getElementById("suggestion-form"),
  suggestionServer: document.getElementById("suggestion-server"),
  suggestionText: document.getElementById("suggestion-text"),
  suggestionList: document.getElementById("suggestion-list"),
  messages: document.getElementById("messages"),
  messageForm: document.getElementById("message-form"),
  messageInput: document.getElementById("message-input"),
  currentChannelTitle: document.getElementById("current-channel-title"),
  currentUserPill: document.getElementById("current-user-pill"),
};

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

function getUserById(userId) {
  return state.appData.users.find((user) => user.id === userId) || null;
}

function getServerById(serverId) {
  return state.appData.servers.find((server) => server.id === serverId) || null;
}

async function refreshState() {
  const data = await apiFetch("/api/state", { method: "GET" });
  state.appData = data;
  state.currentUserId = data.current_user ? data.current_user.id : null;

  if (!state.activeThread && data.servers.length) {
    state.activeThreadType = "server";
    state.activeThread = data.servers[0].id;
  } else if (!state.activeThread && data.dm_threads.length) {
    state.activeThreadType = "dm";
    state.activeThread = data.dm_threads[0].id;
  }

  const userOptions = data.users
    .map((user) => `<option value="${user.id}">${user.name} (${user.skew_code})</option>`)
    .join("");
  elements.loginUser.innerHTML = userOptions || '<option value="">No users</option>';

  const serverOptions = (data.servers || [])
    .map((server) => `<option value="${server.id}">${server.name}</option>`)
    .join("");
  elements.suggestionServer.innerHTML = serverOptions || '<option value="">No servers</option>';

  if (data.current_user) {
    elements.currentUserPill.textContent = `${data.current_user.name} · ${data.current_user.skew_code}`;
  } else {
    elements.currentUserPill.textContent = "Not logged in";
  }

  renderServers(data.servers || []);
  renderUsers(data.users || []);
  renderDMs(data.dm_threads || []);
  renderSuggestions(data.suggestions || []);
  renderMessages();
}

function renderServers(servers) {
  if (!servers.length) {
    elements.serverList.innerHTML = "<p>No servers yet.</p>";
    return;
  }

  elements.serverList.innerHTML = servers
    .map((server) => {
      const isOwner = state.currentUserId && server.owner_id === state.currentUserId;
      return `
        <div class="server-card">
          <strong>${server.name}</strong>
          <div>${server.description}</div>
          <div>Invite: ${server.invite_code}</div>
          <button data-server-id="${server.id}" data-action="select-server">Open</button>
          ${isOwner ? `<button data-server-id="${server.id}" data-action="delete-server" class="secondary">Delete</button>` : ""}
        </div>
      `;
    })
    .join("");

  elements.serverList.querySelectorAll("button[data-action='select-server']").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeThreadType = "server";
      state.activeThread = button.dataset.serverId;
      renderMessages();
    });
  });

  elements.serverList.querySelectorAll("button[data-action='delete-server']").forEach((button) => {
    button.addEventListener("click", async () => {
      await apiFetch(`/api/servers/${button.dataset.serverId}`, { method: "DELETE" });
      await refreshState();
    });
  });
}

function renderUsers(users) {
  if (!users.length) {
    elements.userList.innerHTML = "<p>No users loaded.</p>";
    return;
  }

  const currentUser = users.find((user) => user.id === state.currentUserId);
  const blocked = currentUser?.blocked_users || [];

  elements.userList.innerHTML = users
    .map((user) => {
      const isCurrent = user.id === state.currentUserId;
      const isBlocked = blocked.includes(user.id);
      const actions = isCurrent
        ? "<small>You</small>"
        : `
          <button data-user-id="${user.id}" data-action="dm-user">Message</button>
          <button data-user-id="${user.id}" data-action="block-user" class="secondary">${isBlocked ? "Unblock" : "Block"}</button>
        `;

      return `
        <div class="member-item">
          <strong>${user.name}</strong>
          <div>${user.skew_code} · ${user.status}</div>
          ${actions}
        </div>
      `;
    })
    .join("");

  elements.userList.querySelectorAll("button[data-action='dm-user']").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!state.currentUserId) {
        alert("Please log in first.");
        return;
      }
      const userId = button.dataset.userId;
      const data = await apiFetch("/api/dm", {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      });
      state.activeThreadType = "dm";
      state.activeThread = data.thread.id;
      await refreshState();
    });
  });

  elements.userList.querySelectorAll("button[data-action='block-user']").forEach((button) => {
    button.addEventListener("click", async () => {
      const userId = button.dataset.userId;
      const isBlocked = blocked.includes(userId);
      await apiFetch(isBlocked ? `/api/users/${userId}/unblock` : `/api/users/${userId}/block`, { method: "POST" });
      await refreshState();
    });
  });
}

function renderDMs(dmThreads) {
  if (!dmThreads.length) {
    elements.dmList.innerHTML = "<p>No direct messages yet.</p>";
    return;
  }

  elements.dmList.innerHTML = dmThreads
    .map((thread) => {
      const names = thread.participants
        .map((participantId) => getUserById(participantId)?.name || "Unknown")
        .filter(Boolean)
        .join(", ");
      return `
        <div class="dm-card">
          <strong>${names}</strong>
          <button data-thread-id="${thread.id}" data-thread-type="dm">Open chat</button>
        </div>
      `;
    })
    .join("");

  elements.dmList.querySelectorAll("button[data-thread-type='dm']").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeThreadType = "dm";
      state.activeThread = button.dataset.threadId;
      renderMessages();
    });
  });
}

function renderSuggestions(suggestions) {
  if (!suggestions.length) {
    elements.suggestionList.innerHTML = "<p>No suggestions yet.</p>";
    return;
  }

  elements.suggestionList.innerHTML = suggestions
    .map((suggestion) => {
      const server = getServerById(suggestion.server_id);
      const user = getUserById(suggestion.user_id);
      return `
        <div class="suggestion-item">
          <strong>${user ? user.name : "User"}</strong>
          <div>${server ? server.name : "Unknown server"}</div>
          <div>${suggestion.text}</div>
        </div>
      `;
    })
    .join("");
}

function renderMessages() {
  const currentThreadType = state.activeThreadType || "server";
  const currentThreadId = state.activeThread;

  const messages = [];
  let title = "Choose a chat";

  if (currentThreadType === "server" && currentThreadId) {
    const server = getServerById(currentThreadId);
    if (server) {
      title = `${server.name} · ${server.channels[0] || "general"}`;
      messages.push(...(server.messages || []));
    }
  }

  if (currentThreadType === "dm" && currentThreadId) {
    const thread = state.appData.dm_threads.find((item) => item.id === currentThreadId);
    if (thread) {
      const names = thread.participants
        .map((id) => getUserById(id)?.name || "Unknown")
        .join(", ");
      title = `Direct message · ${names}`;
      messages.push(...(thread.messages || []));
    }
  }

  elements.currentChannelTitle.textContent = title;
  if (!messages.length) {
    elements.messages.innerHTML = "<p>No messages yet in this chat.</p>";
    return;
  }

  elements.messages.innerHTML = messages
    .map((message) => `
      <div class="message-item">
        <strong>${message.user_name}</strong>
        <div>${message.text}</div>
        <div class="message-meta">${message.created_at}</div>
      </div>
    `)
    .join("");
}

async function registerUser(event) {
  event.preventDefault();
  const name = elements.registerName.value.trim();
  if (!name) {
    alert("Please enter a name.");
    return;
  }

  await apiFetch("/api/register", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

  elements.registerForm.reset();
  await refreshState();
}

async function loginUser(event) {
  event.preventDefault();
  const selectedUserId = elements.loginUser.value;
  if (!selectedUserId) {
    alert("Select a user to log in.");
    return;
  }

  await apiFetch("/api/login", {
    method: "POST",
    body: JSON.stringify({ user_id: selectedUserId }),
  });
  await refreshState();
}

async function logoutUser() {
  await apiFetch("/api/logout", { method: "POST" });
  await refreshState();
}

async function createServer(event) {
  event.preventDefault();
  if (!state.currentUserId) {
    alert("Log in before creating a server.");
    return;
  }

  const name = elements.serverName.value.trim();
  const description = elements.serverDescription.value.trim();
  if (!name) {
    alert("Server name is required.");
    return;
  }

  const data = await apiFetch("/api/servers", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });

  state.activeThreadType = "server";
  state.activeThread = data.server.id;
  elements.createServerForm.reset();
  await refreshState();
}

async function joinServer(event) {
  event.preventDefault();
  const inviteCode = elements.inviteCode.value.trim();
  if (!inviteCode) {
    alert("Enter an invite code.");
    return;
  }

  const data = await apiFetch("/api/servers/join", {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });

  state.activeThreadType = "server";
  state.activeThread = data.server.id;
  elements.joinServerForm.reset();
  await refreshState();
}

async function sendMessage(event) {
  event.preventDefault();
  const text = elements.messageInput.value.trim();
  if (!text) {
    return;
  }

  if (!state.activeThread) {
    alert("Pick a chat before sending a message.");
    return;
  }

  if (state.activeThreadType === "server") {
    await apiFetch(`/api/servers/${state.activeThread}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  } else {
    await apiFetch(`/api/dm/${state.activeThread}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  elements.messageInput.value = "";
  await refreshState();
}

async function submitSuggestion(event) {
  event.preventDefault();
  if (!state.currentUserId) {
    alert("Log in to add a suggestion.");
    return;
  }

  const serverId = elements.suggestionServer.value;
  const text = elements.suggestionText.value.trim();
  if (!serverId || !text) {
    alert("Choose a server and add a suggestion request.");
    return;
  }

  await apiFetch("/api/suggestions", {
    method: "POST",
    body: JSON.stringify({ server_id: serverId, text }),
  });

  elements.suggestionForm.reset();
  await refreshState();
}

elements.registerForm.addEventListener("submit", registerUser);
elements.loginForm.addEventListener("submit", loginUser);
elements.logoutButton.addEventListener("click", logoutUser);
elements.createServerForm.addEventListener("submit", createServer);
elements.joinServerForm.addEventListener("submit", joinServer);
elements.messageForm.addEventListener("submit", sendMessage);
elements.suggestionForm.addEventListener("submit", submitSuggestion);

refreshState().catch((error) => {
  console.error(error);
  alert(error.message);
});
