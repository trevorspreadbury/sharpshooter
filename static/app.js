const POLL_INTERVAL_MS = 125;

const runtimeState = {
  requestInFlight: false,
  speedSelectFocused: false,
  pollHandle: null,
  queuedRequest: null,
};

function getGameShell() {
  return document.getElementById("game-shell");
}

function replaceGameShell(markup) {
  const shell = getGameShell();
  if (!shell) {
    return;
  }

  const next = document.createElement("div");
  next.innerHTML = markup.trim();
  const replacement = next.firstElementChild;
  if (replacement) {
    shell.replaceWith(replacement);
  }
}

async function performRequest(request) {
  runtimeState.requestInFlight = true;
  try {
    const response = await fetch(request.url, {
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "fetch",
      },
      ...request.options,
    });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    replaceGameShell(await response.text());
  } finally {
    runtimeState.requestInFlight = false;
    const queuedRequest = runtimeState.queuedRequest;
    runtimeState.queuedRequest = null;
    if (queuedRequest) {
      void performRequest(queuedRequest);
    }
  }
}

function requestMarkup(url, options = {}, priority = "snapshot") {
  const request = {url, options, priority};

  if (!runtimeState.requestInFlight) {
    void performRequest(request);
    return;
  }

  if (priority === "action" || runtimeState.queuedRequest === null) {
    runtimeState.queuedRequest = request;
  }
}

function startPolling() {
  if (runtimeState.pollHandle !== null) {
    return;
  }

  runtimeState.pollHandle = window.setInterval(() => {
    if (runtimeState.requestInFlight || runtimeState.speedSelectFocused) {
      return;
    }
    requestMarkup("/snapshot", {}, "snapshot");
  }, POLL_INTERVAL_MS);
}

document.addEventListener("pointerdown", (event) => {
  const fireButton = event.target.closest("[data-fire-url]");
  if (fireButton instanceof HTMLButtonElement) {
    event.preventDefault();
    requestMarkup(fireButton.dataset.fireUrl, {method: "POST"}, "action");
    return;
  }
});

document.addEventListener("submit", (event) => {
  const form = event.target.closest("form[data-async-post]");
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  event.preventDefault();
  requestMarkup(form.dataset.asyncPost, {
    method: "POST",
    body: new FormData(form),
  }, "action");
});

document.addEventListener("change", (event) => {
  const speedSelect = event.target.closest(".speed-select");
  if (!(speedSelect instanceof HTMLSelectElement)) {
    return;
  }

  runtimeState.speedSelectFocused = false;
  const form = speedSelect.closest("form[data-async-post]");
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  requestMarkup(form.dataset.asyncPost, {
    method: "POST",
    body: new FormData(form),
  }, "action");
});

document.addEventListener("focusin", (event) => {
  if (event.target.closest(".speed-select")) {
    runtimeState.speedSelectFocused = true;
  }
});

document.addEventListener("focusout", (event) => {
  if (event.target.closest(".speed-select")) {
    runtimeState.speedSelectFocused = false;
  }
});

startPolling();
