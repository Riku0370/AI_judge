const historySearchInput = document.getElementById("historySearchInput");
const filterTabs = document.querySelectorAll(".filter-tab");
const historyList = document.getElementById("historyList");
const historyStatus = document.getElementById("historyStatus");
const prevPageButton = document.getElementById("prevPageButton");
const nextPageButton = document.getElementById("nextPageButton");
const pageIndicator = document.getElementById("pageIndicator");

let activeClassName = "";
let searchTimer = null;
let currentPage = 1;
let totalPages = 1;


async function loadPredictionHistory() {
  const query = historySearchInput.value.trim();
  const params = new URLSearchParams({
    page: String(currentPage),
    per_page: "6"
  });

  if (query) {
    params.set("q", query);
  }

  if (activeClassName) {
    params.set("class_name", activeClassName);
  }

  try {
    historyStatus.textContent = "履歴を読み込んでいます";
    historyList.innerHTML = '<p class="empty-text">履歴を読み込んでいます</p>';

    const response = await fetch(`/api/predictions/history?${params.toString()}`);
    if (!response.ok) {
      throw new Error("履歴APIの呼び出しに失敗しました");
    }

    const data = await response.json();
    totalPages = data.total_pages;
    renderPredictionHistory(data.items);
    updatePagination(data);
  } catch (error) {
    historyList.innerHTML = '<p class="empty-text">判定履歴の読み込みに失敗しました</p>';
    historyStatus.textContent = "履歴の読み込みに失敗しました";
  }
}


function updatePagination(data) {
  currentPage = data.page;
  totalPages = data.total_pages;

  historyStatus.textContent = `${data.total}件中 ${data.items.length}件を表示中`;
  pageIndicator.textContent = `${currentPage} / ${totalPages}`;
  prevPageButton.disabled = currentPage <= 1;
  nextPageButton.disabled = currentPage >= totalPages;
}


function openPredictionOnTopPage(predictionId) {
  window.location.href = `/?prediction_id=${predictionId}`;
}


function renderPredictionHistory(history) {
  if (!history.length) {
    historyList.innerHTML = '<p class="empty-text">条件に合う履歴はありません</p>';
    return;
  }

  historyList.innerHTML = "";

  history.forEach((item) => {
    const confidencePercent = (item.confidence * 100).toFixed(2);
    const label = item.class_name === "real" ? "実写画像" : "AI生成画像";

    const card = document.createElement("div");
    card.className = "history-card";
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `${item.filename}を判定画面で開く`);

    const thumbnail = document.createElement("img");
    thumbnail.className = "history-card-image";
    thumbnail.src = item.thumbnail_data_url;
    thumbnail.alt = `${item.filename}のサムネイル`;

    const body = document.createElement("div");
    body.className = "history-card-body";

    const filename = document.createElement("div");
    filename.className = "history-card-name";
    filename.title = item.filename;
    filename.textContent = item.filename;

    const summary = document.createElement("div");
    summary.className = "history-card-summary";
    summary.textContent = `${label} / ${confidencePercent}%`;

    body.append(filename, summary);
    card.append(thumbnail, body);
    card.addEventListener("click", () => openPredictionOnTopPage(item.id));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        openPredictionOnTopPage(item.id);
      }
    });
    historyList.appendChild(card);
  });
}


historySearchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    currentPage = 1;
    loadPredictionHistory();
  }, 250);
});

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    filterTabs.forEach((button) => button.classList.remove("active"));
    tab.classList.add("active");
    activeClassName = tab.dataset.className;
    currentPage = 1;
    loadPredictionHistory();
  });
});

prevPageButton.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage -= 1;
    loadPredictionHistory();
  }
});

nextPageButton.addEventListener("click", () => {
  if (currentPage < totalPages) {
    currentPage += 1;
    loadPredictionHistory();
  }
});

loadPredictionHistory();
