/* Match continuity and direction rules to QC issues. No network and no model call. */
(function (root) {
  const TOPICS = [
    {
      id: "appearance",
      words: ["face", "identity", "duplicate", "look-alike", "lookalike", "eye", "glow", "anatomy", "limb"],
      continuity: ["identity", "eye_glow"],
      direction: [],
    },
    {
      id: "costume",
      words: ["costume", "wardrobe", "hair", "outfit", "garment", "cape"],
      continuity: ["costume"],
      direction: [],
    },
    {
      id: "position",
      words: ["position", "side", "facing", "posture", "eyeline", "gaze", "axis", "blocking"],
      continuity: ["position", "posture", "eyeline"],
      direction: ["sb_axis_eyeline_continuity"],
    },
    {
      id: "travel",
      words: ["walk", "direction", "reverse", "turn"],
      continuity: ["direction"],
      direction: ["sb_axis_eyeline_continuity"],
    },
    {
      id: "props",
      words: ["prop", "sword", "weapon", "hand", "missing", "off-screen", "offscreen"],
      continuity: ["props", "inventory"],
      direction: ["sb_derivative_state_matches_shot"],
    },
    {
      id: "background",
      words: ["background", "location", "plate", "set", "light", "lighting", "damage", "wound", "crack"],
      continuity: ["location_plate", "lighting", "damage"],
      direction: [],
    },
    {
      id: "scene_anchors",
      words: ["anchor", "continuity", "costume", "wound", "prop"],
      continuity: [],
      direction: ["dm_continuity_anchors_per_character"],
    },
  ];

  const STANDING = [
    { ids: ["rule_costume_matches_ref"], category: "costume" },
    { ids: ["rule_exactly_one_identity"], category: "identity" },
    { ids: ["rule_position_lock"], category: "position" },
    { ids: ["rule_prop_state", "rule_location_plate"], category: "props and background" },
  ];

  function hasWord(text, word) {
    const escaped = word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`\\b${escaped}\\b`, "i").test(text);
  }

  function anyWord(text, words) {
    return words.some((word) => hasWord(text, word));
  }

  function topicIdsForIssue(issue) {
    const text = String(issue.description || "");
    const matched = TOPICS.filter((topic) => anyWord(text, topic.words)).map((topic) => topic.id);
    if (matched.length) return matched;
    if (issue.category === "character") return ["appearance"];
    if (issue.category === "continuity") return ["scene_anchors"];
    return [];
  }

  function continuityOrder(topic, text) {
    if (topic.id === "appearance" && (hasWord(text, "eye") || hasWord(text, "glow"))) {
      return ["eye_glow", "identity"];
    }
    if (topic.id === "position") {
      if (hasWord(text, "eyeline") || hasWord(text, "gaze")) return ["eyeline", "posture", "position"];
      if (hasWord(text, "posture")) return ["posture", "position", "eyeline"];
    }
    if (topic.id === "props" && (hasWord(text, "missing") || hasWord(text, "off-screen") || hasWord(text, "offscreen"))) {
      return ["inventory", "props"];
    }
    if (topic.id === "background") {
      if (hasWord(text, "light") || hasWord(text, "lighting")) return ["lighting", "location_plate", "damage"];
      if (hasWord(text, "damage") || hasWord(text, "wound") || hasWord(text, "crack")) {
        return ["damage", "location_plate", "lighting"];
      }
    }
    return topic.continuity;
  }

  function findContinuity(rules, category) {
    return rules.find((rule) => rule.category === category) || null;
  }

  function findDirection(rules, id) {
    return rules.find((rule) => rule.id === id) || null;
  }

  function card(source, category, text, timestamps) {
    return {
      source,
      category,
      text,
      timestamps: [...timestamps].sort((a, b) => a - b),
    };
  }

  function standingItems(continuityRules) {
    const items = [];
    for (const check of STANDING) {
      const rules = check.ids
        .map((id) => continuityRules.find((rule) => rule.id === id))
        .filter(Boolean);
      if (!rules.length) continue;
      items.push(card(
        "Continuity",
        rules.length > 1 ? check.category : rules[0].category,
        rules.map((rule) => rule.rule_text).join("\n\n"),
        [],
      ));
    }
    return items;
  }

  function matchSuggestions(input) {
    const issues = input.issues || [];
    const continuityRules = input.continuityRules || [];
    const directionRules = input.directionRules || [];
    const analysisStatus = input.analysisStatus || "";
    if (!continuityRules.length && !directionRules.length) {
      return { note: "No direction suggestions were found.", items: [] };
    }
    if (analysisStatus !== "complete") {
      return {
        note: "Suggestions are not tied to this episode because the vision pass did not finish.",
        items: [],
      };
    }
    if (!issues.length) {
      return {
        note: "No continuity issues were found. These checks still apply.",
        items: standingItems(continuityRules),
      };
    }

    const byTopic = new Map();
    for (const issue of issues) {
      for (const topicId of topicIdsForIssue(issue)) {
        if (!byTopic.has(topicId)) byTopic.set(topicId, []);
        byTopic.get(topicId).push(issue);
      }
    }

    const items = [];
    const usedDirection = new Set();
    for (const topic of TOPICS) {
      const matched = byTopic.get(topic.id);
      if (!matched) continue;
      const text = matched.map((issue) => issue.description || "").join(" ");
      const stamps = matched
        .map((issue) => Number(issue.timestamp_sec))
        .filter((stamp) => !Number.isNaN(stamp));
      const continuity = continuityOrder(topic, text)
        .map((category) => findContinuity(continuityRules, category))
        .find(Boolean);
      if (continuity) {
        items.push(card("Continuity", continuity.category, continuity.rule_text, stamps));
      }
      for (const ruleId of topic.direction) {
        if (usedDirection.has(ruleId)) {
          const existing = items.find((item) => item.ruleId === ruleId);
          if (existing) {
            existing.timestamps = [...new Set([...existing.timestamps, ...stamps])].sort((a, b) => a - b);
          }
          continue;
        }
        const direction = findDirection(directionRules, ruleId);
        if (!direction) continue;
        usedDirection.add(ruleId);
        const suggestion = card("Direction", direction.category, direction.rule_text, stamps);
        suggestion.ruleId = ruleId;
        items.push(suggestion);
      }
    }

    const visible = items.slice(0, 6).map((item) => ({
      source: item.source,
      category: item.category,
      text: item.text,
      timestamps: item.timestamps,
    }));
    if (!visible.length) {
      return { note: "No direction suggestions were found.", items: [] };
    }
    return {
      note: "Based on the issues found in this episode.",
      items: visible,
    };
  }

  root.qcSuggestions = { matchSuggestions };
})(typeof window !== "undefined" ? window : globalThis);
