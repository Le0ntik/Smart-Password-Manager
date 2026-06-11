const API_URL = "";

let allEntries = [];
let lastEntriesJson = "";


async function loadEntries() {
    const res = await fetch(API_URL + "/entries");
    const data = await res.json();

    const newEntriesJson = JSON.stringify(data);

    if (newEntriesJson === lastEntriesJson) {
        return;
    }

    lastEntriesJson = newEntriesJson;
    allEntries = data;

    renderEntries();
}


function renderEntries() {
    const container = document.getElementById("entries");
    const count = document.getElementById("count");
    const searchInput = document.getElementById("search");

    const searchValue = searchInput ? searchInput.value.toLowerCase().trim() : "";

    container.innerHTML = "";

    const filteredEntries = allEntries
        .map((entry, originalIndex) => ({ entry, originalIndex }))
        .filter(({ entry }) => {
            const title = (entry.title || "").toLowerCase();
            const username = (entry.username || "").toLowerCase();

            return title.includes(searchValue) || username.includes(searchValue);
        });

    if (count) {
        count.textContent = filteredEntries.length;
    }

    if (filteredEntries.length === 0) {
        container.innerHTML = `
            <div class="empty">
                <div class="e-icon">🔐</div>
                <p>Записей пока нет</p>
            </div>
        `;
        return;
    }

    filteredEntries.forEach(({ entry, originalIndex }) => {
        const div = document.createElement("div");
        div.className = "entry";

        const realPassword = entry.password || "";

        div.innerHTML = `
            <div class="entry-icon">🔑</div>

            <div class="entry-info">
                <div class="entry-title">${escapeHtml(entry.title || "Без названия")}</div>

                <div class="entry-meta">
                    <span>👤 ${escapeHtml(entry.username || "")}</span>

                    <span>
                        🔒
                        <span class="password-text">
                            ${maskPassword(realPassword)}
                        </span>
                    </span>

                    <span>📝 ${escapeHtml(entry.note || "—")}</span>
                </div>
            </div>

            <div class="entry-actions">
                <button type="button" class="icon-btn toggle-entry-password" title="Показать пароль">
                    👁
                </button>

                <button type="button" class="icon-btn danger" onclick="deleteEntry(${originalIndex})" title="Удалить">
                    🗑
                </button>
            </div>
        `;

        const passwordText = div.querySelector(".password-text");
        const toggleButton = div.querySelector(".toggle-entry-password");

        let isHidden = true;

        toggleButton.addEventListener("click", () => {
            if (isHidden) {
                passwordText.textContent = realPassword;
                toggleButton.textContent = "🙈";
                toggleButton.title = "Скрыть пароль";
                isHidden = false;
            } else {
                passwordText.textContent = maskPassword(realPassword);
                toggleButton.textContent = "👁";
                toggleButton.title = "Показать пароль";
                isHidden = true;
            }
        });

        container.appendChild(div);
    });
}


async function addEntry() {
    const title = document.getElementById("title").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const note = document.getElementById("note").value.trim();

    if (!title || !username || !password) {
        showToast("Заполните название, логин и пароль");
        return;
    }

    const entry = {
        title: title,
        username: username,
        password: password,
        note: note
    };

    const res = await fetch(API_URL + "/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(entry)
    });

    if (!res.ok) {
        showToast("Ошибка при добавлении записи");
        return;
    }

    document.getElementById("title").value = "";
    document.getElementById("username").value = "";
    document.getElementById("password").value = "";
    document.getElementById("note").value = "";

    updateStrength("");

    showToast("Запись добавлена");

    await loadEntries();
}


async function deleteEntry(index) {
    await fetch(API_URL + "/delete/" + index, {
        method: "DELETE"
    });

    showToast("Запись удалена");

    await loadEntries();
}


function togglePw(inputId, button) {
    const input = document.getElementById(inputId);

    if (!input) {
        return;
    }

    if (input.type === "password") {
        input.type = "text";
        button.textContent = "🙈";
    } else {
        input.type = "password";
        button.textContent = "👁";
    }
}


function maskPassword(password) {
    if (!password) {
        return "";
    }

    return "•".repeat(8);
}


function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function updateStrength(password) {
    const segments = [
        document.getElementById("s1"),
        document.getElementById("s2"),
        document.getElementById("s3"),
        document.getElementById("s4")
    ];

    segments.forEach(segment => {
        if (segment) {
            segment.style.background = "var(--border)";
        }
    });

    let strength = 0;

    if (password.length >= 6) strength++;
    if (password.length >= 10) strength++;
    if (/[A-ZА-Я]/.test(password) && /[a-zа-я]/.test(password)) strength++;
    if (/[0-9]/.test(password) || /[^A-Za-zА-Яа-я0-9]/.test(password)) strength++;

    for (let i = 0; i < strength; i++) {
        if (segments[i]) {
            if (strength <= 1) {
                segments[i].style.background = "#ff4a6a";
            } else if (strength <= 2) {
                segments[i].style.background = "#ffb84a";
            } else if (strength <= 3) {
                segments[i].style.background = "#ffe84a";
            } else {
                segments[i].style.background = "#4fffb0";
            }
        }
    }
}


function showToast(text) {
    const toast = document.getElementById("toast");

    if (!toast) {
        alert(text);
        return;
    }

    toast.textContent = text;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}


document.addEventListener("DOMContentLoaded", () => {
    loadEntries();

    setInterval(loadEntries, 30000);
});