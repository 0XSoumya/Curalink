const BASE_URL = "https://curalink-83o7.onrender.com";

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