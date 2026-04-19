const JSON_HEADERS = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

async function request(path, init = {}) {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${init.method || "GET"} ${path} failed: ${response.status} ${body}`);
  }
  return response.json();
}

function hasSessionTitle(title) {
  return typeof title === "string" && title.trim() !== "";
}

export const api = {
  getSession() {
    return request("/api/session");
  },
  listSessions() {
    return request("/api/sessions");
  },
  createSession(title) {
    const init = { method: "POST" };
    if (hasSessionTitle(title)) {
      init.headers = JSON_HEADERS;
      init.body = JSON.stringify({ title });
    }
    return request("/api/sessions", init);
  },
  activateSession(id) {
    return request(`/api/sessions/${id}/activate`, {
      method: "POST",
    });
  },
  renameSession(id, title) {
    return request(`/api/sessions/${id}`, {
      method: "PATCH",
      headers: JSON_HEADERS,
      body: JSON.stringify({ title }),
    });
  },
  getParticipants() {
    return request("/api/participants");
  },
  getMessages() {
    return request("/api/messages");
  },
  postMessage(message) {
    return request("/api/messages", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(message),
    });
  },
};
