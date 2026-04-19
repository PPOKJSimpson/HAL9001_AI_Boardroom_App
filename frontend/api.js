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

export const api = {
  getSession() {
    return request("/api/session");
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
