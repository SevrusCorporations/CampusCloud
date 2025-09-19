async function fetchUserData() {
  try {
    const res = await fetch("/fetch/userData", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include" // include session cookie
    });

    if (!res.ok) {
      throw new Error("Failed to fetch user data");
    }

    const data = await res.json();

    // Format nicely instead of JSON dump
    const userDiv = document.getElementById("userData");
    userDiv.innerHTML = `
      <p><strong>User ID:</strong> ${data.user_id}</p>
      <p><strong>Name:</strong> ${data.name}</p>
      <p><strong>Role:</strong> ${data.role}</p>
    `;
  } catch (err) {
    document.getElementById("userData").innerText = "Error fetching user data.";
  }
}

document.getElementById("logoutBtn").addEventListener("click", async () => {
  try {
    const res = await fetch("/logout", {
      method: "GET",
      credentials: "include"
    });

    if (res.redirected) {
      window.location.href = res.url;
    } else {
      window.location.href = "/login";
    }
  } catch (err) {
    alert("Logout failed, please try again.");
  }
});

// Fetch data on page load
window.onload = fetchUserData;
