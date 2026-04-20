const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// 🔹 Create new session
export async function createSession() {
  const res = await fetch(`${BASE_URL}/session`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error("Failed to create session");
  }

  return await res.json();
}

// 🔹 Send chat message
export async function sendMessage(payload) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to send message");
  }

  return await res.json();
}

// 🔹 Fetch all sessions for the sidebar
export async function getSessions() {
  const res = await fetch(`${BASE_URL}/sessions`);
  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }
  return await res.json();
}

// 🔹 Fetch a single session's history
export async function getSession(sessionId) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}`);
  if (!res.ok) {
    throw new Error("Failed to fetch session details");
  }
  return await res.json();
}