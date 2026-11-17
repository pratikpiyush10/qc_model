const TERMINAL = new Set(["ready", "failed"]);

const REASON_LABELS = {
  opening: "Opening",
  scene_change: "Scene change",
  interval: "Interval",
  ending: "Ending",
};

const STATUS_LABELS = {
  queued: "Queued",
  extracting: "Extracting",
  analyzing: "Analyzing",
  ready: "Ready",
  failed: "Failed",
};

const ANALYSIS_LABELS = {
  not_configured: "AI analysis not run",
  running: "Analyzing frames",
  complete: "Analysis complete",
  failed: "Analysis failed",
};

const ANALYSIS_CLASS = {
  not_configured: "is-idle",
  running: "is-running",
  complete: "is-complete",
  failed: "is-failed",
};

const SEVERITY_LABELS = {
  info: "Low",
  warning: "Medium",
  error: "High",
};

function limitDescription(text) {
  const value = String(text || "");
  if (value.length <= 350) return value;
  const room = 347;
  let clipped = value.slice(0, room).trimEnd();
  const space = clipped.lastIndexOf(" ");
  if (space >= room - 40) clipped = clipped.slice(0, space).trimEnd();
  return `${clipped}...`;
}

const uploadView = document.getElementById("upload-view");
const progressView = document.getElementById("progress-view");
const resultsView = document.getElementById("results-view");
const rulesView = document.getElementById("rules-view");
const directionView = document.getElementById("direction-view");
const directionList = document.getElementById("direction-list");
const directionStatus = document.getElementById("direction-status");
const guideMenu = document.getElementById("guide-menu");
const directorView = document.getElementById("director-view");
const directorStatus = document.getElementById("director-status");
const directorShows = document.getElementById("director-shows");
const directorDetail = document.getElementById("director-detail");
const directorRules = document.getElementById("director-rules");
const rulesList = document.getElementById("rules-list");
const rulesStatus = document.getElementById("rules-status");
const dropzone = document.getElementById("dropzone");
const dropTitle = document.getElementById("drop-title");
const dropSub = document.getElementById("drop-sub");
const fileInput = document.getElementById("file");
const uploadForm = document.getElementById("upload-form");
const submitButton = document.getElementById("submit");
const uploadError = document.getElementById("upload-error");
const recent = document.getElementById("recent");
const recentList = document.getElementById("recent-list");
const progressKicker = document.getElementById("progress-kicker");
const progressTitle = document.getElementById("progress-title");
const progressFile = document.getElementById("progress-file");
const progressBar = document.getElementById("progress");
const progressFill = document.getElementById("progress-fill");
const progressPercent = document.getElementById("progress-percent");
const progressMessage = document.getElementById("progress-message");
const progressError = document.getElementById("progress-error");
const progressBack = document.getElementById("progress-back");
const resultsTitle = document.getElementById("results-title");
const resultsMeta = document.getElementById("results-meta");
const resultsNote = document.getElementById("results-note");
const analysisChip = document.getElementById("analysis-chip");
const analysisError = document.getElementById("analysis-error");
const analysisHint = document.getElementById("analysis-hint");
const issueEmpty = document.getElementById("issue-empty");
const issueTable = document.getElementById("issue-table");
const suggestionsBox = document.getElementById("suggestions");
const suggestionsNote = document.getElementById("suggestions-note");
const suggestionsList = document.getElementById("suggestions-list");
const issueList = document.getElementById("issue-list");
const frameGrid = document.getElementById("frame-grid");
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
const lightboxCaption = document.getElementById("lightbox-caption");

let selectedFile = null;
let viewToken = 0;
let pollTimer = null;
let dragDepth = 0;
let uploading = false;

function jobIdFromHash() {
  const match = location.hash.match(/^#\/jobs\/([a-f0-9]{12})$/);
  return match ? match[1] : null;
}

function stopWatching() {
  viewToken += 1;
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = null;
}

async function api(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch (_error) {
      /* The body was not JSON. */
    }
    throw new Error(detail);
  }
  return response.json();
}

function formatTimestamp(seconds) {
  const total = Math.round(Math.max(0, Number(seconds) || 0) * 100);
  const minutes = Math.floor(total / 6000);
  const remainder = total % 6000;
  const whole = Math.floor(remainder / 100);
  const fraction = remainder % 100;
  return `${String(minutes).padStart(2, "0")}:${String(whole).padStart(2, "0")}.${String(fraction).padStart(2, "0")}`;
}

function formatClock(seconds) {
  if (seconds == null || Number.isNaN(Number(seconds))) return "";
  const total = Math.max(0, Math.round(Number(seconds)));
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function show(view) {
  uploadView.hidden = view !== "upload";
  progressView.hidden = view !== "progress";
  resultsView.hidden = view !== "results";
  rulesView.hidden = view !== "rules";
  directionView.hidden = view !== "direction";
  directorView.hidden = view !== "director";
}

function resetPicker() {
  selectedFile = null;
  fileInput.value = "";
  submitButton.disabled = true;
  dropTitle.textContent = "Drop an MP4 here";
}

function selectFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".mp4")) {
    uploadError.hidden = false;
    uploadError.textContent = "Choose an .mp4 video.";
    return;
  }
  selectedFile = file;
  submitButton.disabled = false;
  dropTitle.textContent = file.name;
  dropSub.textContent = formatBytes(file.size);
  uploadError.hidden = true;
}

function setProgress(percent, { failed = false } = {}) {
  const value = Math.max(0, Math.min(100, Math.round(percent)));
  progressFill.style.width = `${value}%`;
  progressBar.setAttribute("aria-valuenow", String(value));
  progressBar.classList.toggle("is-error", failed);
  progressPercent.textContent = `${value}%`;
}

function showWorking({ kicker, title, fileName, progress, message, error = "" }) {
  show("progress");
  progressKicker.textContent = kicker;
  progressTitle.textContent = title;
  progressFile.textContent = fileName || "";
  progressMessage.textContent = message || "";
  setProgress(progress, { failed: Boolean(error) });
  progressError.hidden = !error;
  progressError.textContent = error;
  progressBack.hidden = !error;
}

async function showUpload({ error = "", keepFile = false } = {}) {
  const token = viewToken;
  document.title = "Scene QC";
  show("upload");
  if (!keepFile) resetPicker();
  uploadError.hidden = !error;
  uploadError.textContent = error;
  try {
    const config = await api("/api/config");
    if (token !== viewToken) return;
    if (!selectedFile) {
      dropSub.textContent = `H.264 video, up to ${config.max_upload_mb} MB`;
    }
    const level = config.analysis_level || "high";
    const levelNotes = {
      low: "Vision analysis is set to low and sends 6 small frames.",
      medium: "Vision analysis is set to medium and sends up to 40 frames.",
      high: "Vision analysis is set to high and sends every key frame.",
    };
    analysisHint.hidden = false;
    const modelNote = config.vision_model ? ` Model: ${config.vision_model}.` : "";
    analysisHint.textContent = config.analysis_available
      ? `${levelNotes[level] || `Vision analysis is set to ${level}.`}${modelNote}`
      : "Set LITELLM_API_KEY on the server to run continuity and character checks.";
  } catch (_error) {
    /* The hint can stay on the default size. */
  }
  try {
    const jobs = await api("/api/jobs");
    if (token !== viewToken) return;
    renderRecent(jobs);
  } catch (_error) {
    recent.hidden = true;
  }
}

function renderRecent(jobs) {
  recentList.replaceChildren();
  if (!jobs.length) {
    recent.hidden = true;
    return;
  }
  recent.hidden = false;
  for (const job of jobs) {
    const link = document.createElement("a");
    link.href = `#/jobs/${job.id}`;
    const name = document.createElement("span");
    name.textContent = job.filename;
    const duration = document.createElement("span");
    duration.textContent = formatClock(job.duration_sec);
    const pill = document.createElement("span");
    pill.className = `pill ${job.status}`;
    pill.textContent = STATUS_LABELS[job.status] || job.status;
    link.append(name, duration, pill);
    recentList.append(link);
  }
}

function renderJob(job) {
  document.title = `${job.filename} · Scene QC`;
  if (job.status === "failed") {
    showWorking({
      kicker: "Stopped",
      title: "Extraction failed",
      fileName: job.filename,
      progress: job.progress || 0,
      message: job.message,
      error: job.error || "Extraction failed.",
    });
    return;
  }
  if (job.status !== "ready") {
    showWorking({
      kicker: "In progress",
      title: job.status === "analyzing" ? "Reviewing frames" : "Extracting key frames",
      fileName: job.filename,
      progress: job.progress || 0,
      message: job.message,
    });
    return;
  }
  showResults(job);
}

function showResults(job) {
  show("results");
  resultsTitle.textContent = job.filename;
  const bits = [
    formatClock(job.duration_sec),
    job.fps ? `${job.fps} fps` : "",
    job.width && job.height ? `${job.width}×${job.height}` : "",
    `${job.keyframe_count} key frames`,
  ].filter(Boolean);
  resultsMeta.textContent = bits.join(" · ");
  resultsNote.hidden = !job.limit_note;
  resultsNote.textContent = job.limit_note || "";
  analysisChip.textContent = ANALYSIS_LABELS[job.analysis_status] || ANALYSIS_LABELS.not_configured;
  analysisChip.className = `chip ${ANALYSIS_CLASS[job.analysis_status] || "is-idle"}`;
  const analysisFailed = job.analysis_status === "failed";
  analysisError.hidden = !analysisFailed;
  analysisError.textContent = analysisFailed ? (job.error || "Analysis failed.") : "";
  renderIssues(job);
  renderSuggestions(job);
  renderFrames(job);
}

let suggestionRules = null;
let suggestionToken = 0;

async function loadSuggestionRules() {
  if (suggestionRules) return suggestionRules;
  const [continuity, direction] = await Promise.all([
    api("/api/rules").catch(() => null),
    api("/api/direction").catch(() => null),
  ]);
  if (!continuity && !direction) return null;
  suggestionRules = {
    continuity: continuity || [],
    direction: direction || [],
  };
  return suggestionRules;
}

async function renderSuggestions(job) {
  const token = viewToken;
  const mine = suggestionToken + 1;
  suggestionToken = mine;
  if (!suggestionsBox) return;
  suggestionsBox.hidden = false;
  suggestionsNote.textContent = "Loading suggestions…";
  suggestionsList.replaceChildren();
  const rules = await loadSuggestionRules();
  if (token !== viewToken || mine !== suggestionToken) return;
  if (!rules || typeof qcSuggestions === "undefined") {
    suggestionsNote.textContent = "No direction suggestions were found.";
    return;
  }
  const result = qcSuggestions.matchSuggestions({
    issues: job.issues || [],
    analysisStatus: job.analysis_status,
    continuityRules: rules.continuity,
    directionRules: rules.direction,
  });
  if (token !== viewToken || mine !== suggestionToken) return;
  suggestionsNote.textContent = result.note;
  for (const item of result.items) {
    const card = document.createElement("article");
    card.className = "suggestion-card";
    const meta = document.createElement("p");
    meta.className = "suggestion-meta";
    meta.textContent = `${item.source} · ${categoryLabel(item.category)}`;
    const text = document.createElement("p");
    text.textContent = item.text;
    card.append(meta, text);
    if (item.timestamps && item.timestamps.length) {
      const related = document.createElement("p");
      related.className = "suggestion-related";
      const stamps = [...new Set(item.timestamps.map((stamp) => formatTimestamp(stamp)))];
      related.textContent = `Related issues: ${stamps.join(", ")}`;
      card.append(related);
    }
    suggestionsList.append(card);
  }
}

function renderIssues(job) {
  const issues = job.issues || [];
  issueList.replaceChildren();
  issueEmpty.hidden = issues.length > 0;
  issueTable.hidden = issues.length === 0;
  if (!issues.length) {
    if (job.analysis_status === "complete") {
      issueEmpty.textContent = "No continuity or character issues found.";
    } else if (job.analysis_status === "failed") {
      issueEmpty.textContent = "The vision pass did not finish, so no issues were recorded.";
    } else {
      issueEmpty.textContent = "No issues yet.";
    }
    return;
  }
  for (const issue of issues) {
    const row = document.createElement("tr");
    row.className = `severity-${issue.severity || "info"}`;
    const stampCell = document.createElement("td");
    const stamp = document.createElement("button");
    stamp.type = "button";
    stamp.className = "stamp";
    stamp.textContent = formatTimestamp(issue.timestamp_sec);
    stamp.addEventListener("click", () => focusFrame(job, issue));
    stampCell.append(stamp);
    const typeCell = document.createElement("td");
    typeCell.textContent = categoryLabel(issue.category || "issue");
    const severityCell = document.createElement("td");
    const severity = document.createElement("span");
    const severityKey = issue.severity || "info";
    severity.className = `severity-label severity-${severityKey}`;
    severity.textContent = SEVERITY_LABELS[severityKey] || categoryLabel(severityKey);
    severityCell.append(severity);
    const descriptionCell = document.createElement("td");
    descriptionCell.textContent = limitDescription(issue.description || "");
    const framesCell = document.createElement("td");
    framesCell.className = "issue-frames";
    const names = issue.frame_filenames || [];
    if (!names.length) {
      framesCell.textContent = "None";
    } else {
      for (const name of names) {
        framesCell.append(issueThumb(job, issue, name));
      }
    }
    row.append(stampCell, typeCell, severityCell, descriptionCell, framesCell);
    issueList.append(row);
  }
}

function issueThumb(job, issue, filename) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "issue-thumb";
  const image = document.createElement("img");
  image.src = frameUrl(job.id, filename);
  image.alt = `Frame ${filename}`;
  image.addEventListener("error", () => {
    button.replaceChildren(document.createTextNode(filename));
  });
  button.append(image);
  button.addEventListener("click", () => {
    focusFrame(job, { ...issue, frame_filenames: [filename] });
  });
  return button;
}

function renderFrames(job) {
  frameGrid.replaceChildren();
  for (const frame of job.keyframes || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "frame";
    button.dataset.filename = frame.filename;
    button.dataset.timestamp = String(frame.timestamp_sec);
    const image = document.createElement("img");
    image.src = frameUrl(job.id, frame.filename);
    image.alt = `Key frame at ${formatTimestamp(frame.timestamp_sec)}`;
    const meta = document.createElement("div");
    meta.className = "frame-meta";
    const time = document.createElement("time");
    time.dateTime = `PT${frame.timestamp_sec}S`;
    time.textContent = formatTimestamp(frame.timestamp_sec);
    const reason = document.createElement("span");
    reason.textContent = REASON_LABELS[frame.reason] || frame.reason;
    meta.append(time, reason);
    button.append(image, meta);
    button.addEventListener("click", () => openFrame(job, frame, image.src));
    frameGrid.append(button);
  }
}

function frameUrl(jobId, filename) {
  return `/api/jobs/${encodeURIComponent(jobId)}/frames/${encodeURIComponent(filename)}`;
}

function openFrame(job, frame, src) {
  lightboxImg.src = src;
  lightboxImg.alt = `Key frame at ${formatTimestamp(frame.timestamp_sec)}`;
  const parts = [
    formatTimestamp(frame.timestamp_sec),
    REASON_LABELS[frame.reason] || frame.reason,
  ];
  if (frame.correlation != null) {
    parts.push(`correlation ${Number(frame.correlation).toFixed(2)}`);
  }
  lightboxCaption.textContent = `${job.filename} · ${parts.join(" · ")}`;
  lightbox.showModal();
}

function focusFrame(job, issue) {
  const names = new Set(issue.frame_filenames || []);
  let target = null;
  if (names.size) {
    target = frameGrid.querySelector(`[data-filename="${cssEscape([...names][0])}"]`);
  }
  if (!target) {
    let bestDistance = Infinity;
    for (const button of frameGrid.querySelectorAll(".frame")) {
      const distance = Math.abs(Number(button.dataset.timestamp) - Number(issue.timestamp_sec));
      if (distance < bestDistance) {
        bestDistance = distance;
        target = button;
      }
    }
  }
  if (!target) return;
  for (const button of frameGrid.querySelectorAll(".frame")) {
    button.classList.remove("is-marked");
  }
  target.classList.add("is-marked");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.focus();
}

function cssEscape(value) {
  if (window.CSS && CSS.escape) return CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "");
}

async function watchJob(id) {
  const token = viewToken;

  async function tick() {
    if (token !== viewToken) return;
    let job;
    try {
      job = await api(`/api/jobs/${id}`);
    } catch (error) {
      if (token !== viewToken) return;
      showWorking({
        kicker: "Connection",
        title: "Lost the local server",
        fileName: "",
        progress: 0,
        message: "",
        error: error.message,
      });
      pollTimer = setTimeout(tick, 1000);
      return;
    }
    if (token !== viewToken) return;
    renderJob(job);
    if (!TERMINAL.has(job.status)) {
      pollTimer = setTimeout(tick, 400);
    }
  }

  await tick();
}

function categoryLabel(category) {
  return String(category || "other")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function ruleExample(label, text, kind) {
  const block = document.createElement("p");
  block.className = kind;
  const name = document.createElement("span");
  name.className = "example-label";
  name.textContent = label;
  block.append(name, document.createTextNode(text || "None listed."));
  return block;
}

function renderRules(rules) {
  rulesList.replaceChildren();
  if (!rules.length) {
    rulesStatus.textContent = "No continuity rules found.";
    return;
  }
  rulesStatus.textContent = `${rules.length} rules.`;
  const groups = new Map();
  for (const rule of rules) {
    const key = rule.category || "other";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(rule);
  }
  for (const category of [...groups.keys()].sort()) {
    const section = document.createElement("section");
    section.className = "rule-group";
    const heading = document.createElement("h2");
    heading.textContent = categoryLabel(category);
    section.append(heading);
    for (const rule of groups.get(category)) {
      const card = document.createElement("article");
      card.className = "rule";
      const title = document.createElement("h3");
      title.textContent = rule.rule_text;
      const examples = document.createElement("div");
      examples.className = "rule-examples";
      examples.append(
        ruleExample("Good example", rule.good_example, "example-good"),
        ruleExample("Bad example", rule.bad_example, "example-bad"),
      );
      card.append(title, examples);
      section.append(card);
    }
    rulesList.append(section);
  }
}

async function showRules() {
  const token = viewToken;
  show("rules");
  document.title = "Continuity rules — Scene QC";
  rulesList.replaceChildren();
  rulesStatus.textContent = "Loading rules…";
  try {
    const rules = await api("/api/rules");
    if (token !== viewToken) return;
    renderRules(rules);
  } catch (error) {
    if (token !== viewToken) return;
    rulesStatus.textContent = error.message;
  }
}

function renderDirection(rules) {
  directionList.replaceChildren();
  if (!rules.length) {
    directionStatus.textContent = "No direction rules found.";
    return;
  }
  directionStatus.textContent = `${rules.length} direction rules.`;
  const groups = new Map();
  for (const rule of rules) {
    const key = rule.category || "other";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(rule);
  }
  for (const category of [...groups.keys()].sort()) {
    const section = document.createElement("section");
    section.className = "rule-group";
    const heading = document.createElement("h2");
    heading.textContent = categoryLabel(category);
    section.append(heading);
    for (const rule of groups.get(category)) {
      const card = document.createElement("article");
      card.className = "rule";
      const title = document.createElement("h3");
      title.textContent = rule.rule_text;
      card.append(title);
      if (rule.applies_to) {
        const scope = document.createElement("p");
        scope.className = "rule-scope";
        scope.textContent = categoryLabel(rule.applies_to);
        card.append(scope);
      }
      const quotes = rule.evidence || [];
      if (quotes.length) {
        const examples = document.createElement("div");
        examples.className = "rule-examples";
        for (const item of quotes) {
          const where = [item.show, item.episode].filter(Boolean).join(" · ");
          examples.append(ruleExample(where || "Evidence", item.quote, "example-good"));
        }
        card.append(examples);
      }
      if (rule.notes) {
        const note = document.createElement("p");
        note.className = "rule-note";
        note.textContent = rule.notes;
        card.append(note);
      }
      section.append(card);
    }
    directionList.append(section);
  }
}

async function showDirection() {
  const token = viewToken;
  show("direction");
  document.title = "Direction — Scene QC";
  directionList.replaceChildren();
  directionStatus.textContent = "Loading direction rules…";
  try {
    const rules = await api("/api/direction");
    if (token !== viewToken) return;
    renderDirection(rules);
  } catch (error) {
    if (token !== viewToken) return;
    directionStatus.textContent = error.message;
  }
}

const DIRECTOR_RULE_CATEGORIES = new Set([
  "theme",
  "camera",
  "visual",
  "visual_style",
  "narrative_structure",
  "scene_intent",
  "continuity",
  "transitions",
  "storyboard",
]);

function directorIdFromHash() {
  const match = location.hash.match(/^#\/director\/([A-Za-z0-9._-]+)$/);
  return match ? match[1] : null;
}

function episodeButtonLabel(item) {
  const parts = [item.episode || item.id];
  if (item.version) parts.push(item.version);
  if (item.title) parts.push(item.title);
  return parts.join(" · ");
}

function renderDirectorIndex(episodes, selectedId) {
  directorShows.replaceChildren();
  const groups = new Map();
  for (const episode of episodes) {
    const showName = episode.show || "Other";
    if (!groups.has(showName)) groups.set(showName, []);
    groups.get(showName).push(episode);
  }
  for (const [showName, items] of groups) {
    const section = document.createElement("section");
    section.className = "rule-group";
    const heading = document.createElement("h2");
    heading.textContent = showName;
    const row = document.createElement("div");
    row.className = "show-episodes";
    for (const item of items) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "episode-button";
      if (!item.has_manual) button.classList.add("is-empty");
      button.textContent = episodeButtonLabel(item);
      if (item.id === selectedId) button.setAttribute("aria-current", "page");
      button.addEventListener("click", () => {
        location.hash = `#/director/${encodeURIComponent(item.id)}`;
      });
      row.append(button);
    }
    section.append(heading, row);
    directorShows.append(section);
  }
}

function addFields(parent, fields) {
  for (const field of fields || []) {
    const block = document.createElement("div");
    block.className = "director-field";
    const label = document.createElement("p");
    label.className = "director-label";
    label.textContent = field.label;
    const value = document.createElement("p");
    value.className = "director-value";
    value.textContent = field.value;
    block.append(label, value);
    parent.append(block);
  }
}

function renderDirectorDetail(episode) {
  directorDetail.replaceChildren();
  const head = document.createElement("div");
  head.className = "director-episode";
  const title = document.createElement("h2");
  title.textContent = episodeButtonLabel(episode);
  const showName = document.createElement("p");
  showName.className = "note";
  showName.textContent = episode.show || "";
  head.append(title, showName);
  directorDetail.append(head);
  if (!episode.has_manual) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No director's manual was saved for this episode.";
    directorDetail.append(empty);
    return;
  }
  for (const section of episode.sections || []) {
    const block = document.createElement("section");
    block.className = "rule-group";
    const heading = document.createElement("h2");
    heading.textContent = section.title;
    block.append(heading);
    if (section.heading) {
      const source = document.createElement("p");
      source.className = "rule-scope";
      source.textContent = section.heading;
      block.append(source);
    }
    addFields(block, section.fields);
    if (section.text) {
      const text = document.createElement("p");
      text.className = "director-value";
      text.textContent = section.text;
      block.append(text);
    }
    if (section.table && section.table.header && section.table.rows) {
      const wrap = document.createElement("div");
      wrap.className = "director-table-wrap";
      const table = document.createElement("table");
      table.className = "director-table";
      const thead = document.createElement("thead");
      const headRow = document.createElement("tr");
      for (const cell of section.table.header) {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = cell;
        headRow.append(th);
      }
      thead.append(headRow);
      const tbody = document.createElement("tbody");
      for (const row of section.table.rows) {
        const tr = document.createElement("tr");
        for (const cell of row) {
          const td = document.createElement("td");
          td.textContent = cell;
          tr.append(td);
        }
        tbody.append(tr);
      }
      table.append(thead, tbody);
      wrap.append(table);
      block.append(wrap);
    }
    for (const scene of section.scenes || []) {
      const card = document.createElement("article");
      card.className = "rule";
      const sceneTitle = document.createElement("h3");
      sceneTitle.textContent = scene.heading || "Scene";
      card.append(sceneTitle);
      const meta = [];
      if (scene.shot_range && scene.shot_range.length) {
        const range = scene.shot_range.length === 1
          ? `Shot ${scene.shot_range[0]}`
          : `Shots ${scene.shot_range[0]}–${scene.shot_range[scene.shot_range.length - 1]}`;
        meta.push(range);
      }
      if (scene.stated_duration_s != null) meta.push(`${scene.stated_duration_s}s`);
      if (meta.length) {
        const scope = document.createElement("p");
        scope.className = "rule-scope";
        scope.textContent = meta.join(" · ");
        card.append(scope);
      }
      addFields(card, scene.fields);
      if (scene.text) {
        const text = document.createElement("p");
        text.className = "director-value";
        text.textContent = scene.text;
        card.append(text);
      }
      block.append(card);
    }
    directorDetail.append(block);
  }
}

function renderDirectorRules(rules) {
  directorRules.replaceChildren();
  const picked = (rules || []).filter((rule) => DIRECTOR_RULE_CATEGORIES.has(rule.category));
  if (!picked.length) return;
  const intro = document.createElement("section");
  intro.className = "rule-group";
  const heading = document.createElement("h2");
  heading.textContent = "Key direction rules";
  intro.append(heading);
  const groups = new Map();
  for (const rule of picked) {
    if (!groups.has(rule.category)) groups.set(rule.category, []);
    groups.get(rule.category).push(rule);
  }
  for (const category of [...groups.keys()].sort()) {
    const group = document.createElement("div");
    const label = document.createElement("p");
    label.className = "director-label";
    label.textContent = categoryLabel(category);
    group.append(label);
    for (const rule of groups.get(category)) {
      const line = document.createElement("p");
      line.className = "director-value";
      line.textContent = rule.rule_text;
      group.append(line);
    }
    intro.append(group);
  }
  directorRules.append(intro);
}

async function showDirector() {
  const token = viewToken;
  show("director");
  document.title = "Director's Input — Scene QC";
  directorShows.replaceChildren();
  directorDetail.replaceChildren();
  directorRules.replaceChildren();
  directorStatus.textContent = "Loading director's manuals…";
  const selectedId = directorIdFromHash();
  try {
    const episodes = await api("/api/director");
    if (token !== viewToken) return;
    if (!episodes.length) {
      directorStatus.textContent = "No director's manuals found.";
      return;
    }
    const withManual = episodes.filter((item) => item.has_manual).length;
    directorStatus.textContent = `${episodes.length} episodes, ${withManual} with a director's manual.`;
    renderDirectorIndex(episodes, selectedId);
    try {
      const rules = await api("/api/direction");
      if (token !== viewToken) return;
      renderDirectorRules(rules);
    } catch (_rulesError) {
      /* The episode manuals still render when the rules list fails. */
    }
    if (!selectedId) return;
    const episode = await api(`/api/director/${encodeURIComponent(selectedId)}`);
    if (token !== viewToken) return;
    renderDirectorDetail(episode);
  } catch (error) {
    if (token !== viewToken) return;
    directorStatus.textContent = error.message;
  }
}

function markGuide() {
  const page = location.hash.startsWith("#/rules")
    ? "rules"
    : location.hash.startsWith("#/director")
      ? "director"
      : location.hash.startsWith("#/direction")
        ? "direction"
        : "";
  for (const link of document.querySelectorAll(".guide-option")) {
    if (link.dataset.guide === page) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (guideMenu) guideMenu.open = false;
}

async function route() {
  stopWatching();
  markGuide();
  if (location.hash === "#/rules" || location.hash === "#/rules/") {
    await showRules();
    return;
  }
  if (location.hash === "#/direction" || location.hash === "#/direction/") {
    await showDirection();
    return;
  }
  if (location.hash === "#/director" || location.hash.startsWith("#/director/")) {
    await showDirector();
    return;
  }
  const id = jobIdFromHash();
  if (!id) {
    await showUpload();
    return;
  }
  await watchJob(id);
}

function upload(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/jobs");
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total);
    };
    xhr.onload = () => {
      let body = {};
      try {
        body = JSON.parse(xhr.responseText || "{}");
      } catch (_error) {
        body = {};
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body);
        return;
      }
      reject(new Error(typeof body.detail === "string" ? body.detail : `Upload failed (${xhr.status})`));
    };
    xhr.onerror = () => reject(new Error("Upload failed. Is the local server running?"));
    const body = new FormData();
    body.append("file", file);
    xhr.send(body);
  });
}

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));

dropzone.addEventListener("dragenter", (event) => {
  event.preventDefault();
  dragDepth += 1;
  dropzone.classList.add("is-hot");
});
dropzone.addEventListener("dragover", (event) => event.preventDefault());
dropzone.addEventListener("dragleave", (event) => {
  event.preventDefault();
  dragDepth -= 1;
  if (dragDepth <= 0) {
    dragDepth = 0;
    dropzone.classList.remove("is-hot");
  }
});
dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dragDepth = 0;
  dropzone.classList.remove("is-hot");
  selectFile(event.dataTransfer.files[0]);
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedFile || uploading) return;
  const file = selectedFile;
  uploading = true;
  submitButton.disabled = true;
  showWorking({
    kicker: "Upload",
    title: "Sending the episode",
    fileName: file.name,
    progress: 0,
    message: "Uploading",
  });
  try {
    const job = await upload(file, (fraction) => {
      setProgress(fraction * 100);
      progressMessage.textContent = "Uploading";
    });
    location.hash = `#/jobs/${job.id}`;
  } catch (error) {
    uploading = false;
    submitButton.disabled = !selectedFile;
    await showUpload({ error: error.message, keepFile: true });
    return;
  }
  uploading = false;
  await route();
});

window.addEventListener("hashchange", () => {
  if (uploading) return;
  route();
});

route();
