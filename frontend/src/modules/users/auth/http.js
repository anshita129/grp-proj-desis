export const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
};

export const readJsonSafe = async (res) => {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { _raw: text };
  }
};

export const csrfFetch = async (url, options = {}) => {
  const csrfToken = getCookie("csrftoken");
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    ...(options.headers || {}),
  };
  if (!headers["Content-Type"] && method !== "GET") headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRFToken"] = csrfToken;

  return fetch(url, { credentials: "include", ...options, headers });
};

