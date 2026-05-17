(function () {
  const STORAGE_KEYS = {
    intake: "divination-demo:intake",
    selectedCase: "divination-demo:selected-case",
    importedWorkflow: "divination-demo:workflow"
  };

  const TRACE_STEPS = [
    ["normalize_profile", "字段归一化与缺失标记"],
    ["analyzers", "体系证据生成"],
    ["battle", "张力识别与交叉质询"],
    ["judge", "基于 issue 的裁决收束"],
    ["report", "生成带保留意见的交付稿"]
  ];

  const DEMO_WORKFLOW = {
    request: { query: "请综合分析我的事业和感情趋势", focus_areas: ["career", "relationship"] },
    normalized_profile: { completeness: "exact", missing_fields: [] },
    system_evidence: [{ claims: [1, 2, 3] }, { claims: [4, 5, 6] }],
    debate_issues: [
      {
        dimension: "career",
        relation: "tension",
        question: "事业维度存在张力，哪些现实条件会决定最终偏向？",
        status: "open"
      },
      {
        dimension: "risk",
        relation: "insufficient-data",
        question: "风险维度的资料仍不足，是否存在缺失字段或过低置信度导致暂时无法裁决？",
        status: "open"
      }
    ],
    fusion_report: {
      summary: "问题“请综合分析我的事业和感情趋势”：条件判断为主。",
      consensus_points: ["未形成稳定共识。"],
      disagreement_points: ["事业更偏向八字，但只在条件边界内成立。"],
      reservations: ["存在无法裁决的 issue，结论需与补充资料一起阅读。"],
      suggested_followups: ["继续追问事业：哪些现实条件决定偏向？"]
    },
    trace_metadata: { steps: [1, 2, 3, 4, 5] }
  };

  const CASE_DATA = {
    full: {
      label: "完整",
      note: "完整资料基线。",
      summary: "条件判断为主，保留 2 个未决项。",
      deliveryReadout: "先看条件边界，再看未决项。",
      completeness: "EXACT",
      missingText: "无关键缺口。",
      focusText: "事业 / 感情",
      relationText: "事业有张力，感情收敛，性格与风险保守处理。",
      claims: 6,
      open: 3,
      tension: 1,
      trace: 5,
      chips: [
        { text: "完整资料", color: "var(--accent-jade)" },
        { text: "条件判断", color: "var(--accent-gold)" }
      ],
      nodes: {
        career: "事业存在张力，需保留条件边界",
        relationship: "感情相对收敛",
        personality: "仍未决",
        risk: "风险来自资料敏感度"
      },
      issues: [
        {
          dimension: "事业",
          state: "tension",
          desc: "证据有张力，只能保留条件偏向。",
          rank: "01"
        },
        {
          dimension: "性格",
          state: "insufficient-data",
          desc: "仍未决，需补现实条件。",
          rank: "02"
        },
        {
          dimension: "风险",
          state: "insufficient-data",
          desc: "风险主要来自资料与解释敏感度。",
          rank: "03"
        }
      ],
      sections: {
        consensus: ["未形成稳定共识。"],
        disagreement: [
          "事业更偏向八字，但只在条件边界内成立。",
          "性格与风险仍未决。"
        ],
        reservations: [
          "事业结论需连同前提一起阅读。",
          "存在未裁决 issue。"
        ],
        followups: [
          "继续追问事业：哪些现实条件决定偏向？",
          "继续确认事业边界。"
        ]
      }
    },
    "date-only": {
      label: "缺时辰",
      note: "信息不完整时的降级。",
      summary: "条件判断为主，保留 3 个未决项。",
      deliveryReadout: "先看缺什么，再看影响什么。",
      completeness: "DATE-ONLY",
      missingText: "缺出生时辰。",
      focusText: "健康 / 性格",
      relationText: "性格有张力，其余维度更受缺口影响。",
      claims: 5,
      open: 3,
      tension: 1,
      trace: 5,
      chips: [
        { text: "缺失时辰", color: "var(--accent-gold)" },
        { text: "保守表达", color: "var(--accent)" }
      ],
      nodes: {
        career: "受缺失字段影响",
        relationship: "仅保留概括判断",
        personality: "仍有张力，但置信度下降",
        risk: "提醒来自资料缺口"
      },
      issues: [
        { dimension: "性格", state: "tension", desc: "有交叉解释空间，但不能写满。", rank: "01" },
        { dimension: "关系", state: "insufficient-data", desc: "更多是信息不足，不是真冲突。", rank: "02" },
        { dimension: "事业", state: "insufficient-data", desc: "需要更完整资料。", rank: "03" },
        { dimension: "风险", state: "insufficient-data", desc: "主要不确定性来自数据质量。", rank: "04" }
      ],
      sections: {
        consensus: ["未形成稳定共识。"],
        disagreement: [
          "性格仍有张力，但因缺时辰只能保留条件偏向。",
          "感情、事业、风险更多属于资料不足。"
        ],
        reservations: [
          "缺时辰，结论按保守口径理解。",
          "性格结论需连同前提一起阅读。",
          "存在未裁决 issue。"
        ],
        followups: [
          "优先补时辰。",
          "继续追问性格。",
          "继续确认性格边界。"
        ]
      }
    },
    career: {
      label: "事业",
      note: "单维度交付。",
      summary: "事业为主轴，保留 3 个未决项。",
      deliveryReadout: "只保留事业主轴，其他维度退后。",
      completeness: "EXACT",
      missingText: "无关键缺口，其他维度未展开。",
      focusText: "事业",
      relationText: "事业是唯一主轴，其余维度退后。",
      claims: 5,
      open: 4,
      tension: 1,
      trace: 5,
      chips: [
        { text: "单维度交付", color: "var(--accent)" },
        { text: "条件主轴", color: "var(--accent-gold)" }
      ],
      nodes: {
        career: "唯一主轴，张力需明说",
        relationship: "退到背景层",
        personality: "只保留概括",
        risk: "提示来自条件边界"
      },
      issues: [
        { dimension: "事业", state: "tension", desc: "主轴解释必须集中在条件边界。", rank: "01" },
        { dimension: "关系", state: "insufficient-data", desc: "退到背景信息。", rank: "02" },
        { dimension: "性格", state: "insufficient-data", desc: "保持概括。", rank: "03" },
        { dimension: "风险", state: "insufficient-data", desc: "风险来自条件触发。", rank: "04" }
      ],
      sections: {
        consensus: ["未形成稳定共识。"],
        disagreement: [
          "事业更偏向八字，但只在条件边界内成立。",
          "其余维度仍是背景未决项。"
        ],
        reservations: [
          "事业结论需连同前提一起阅读。",
          "存在未裁决 issue。"
        ],
        followups: [
          "继续追问事业：哪些现实条件决定偏向？",
          "继续确认事业边界。",
          "其余维度保持背景。"
        ]
      }
    }
  };

  function safeRead(key) {
    try {
      const raw = window.sessionStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      return null;
    }
  }

  function safeWrite(key, value) {
    window.sessionStorage.setItem(key, JSON.stringify(value));
  }

  function dimensionLabel(dimension) {
    return (
      {
        career: "事业",
        relationship: "感情",
        personality: "性格",
        risk: "风险",
        health: "健康",
        wealth: "财务"
      }[dimension] || dimension
    );
  }

  function fieldLabel(field) {
    return (
      {
        birth_date: "出生日期",
        birth_time: "出生时辰",
        birth_place: "出生地点",
        timezone: "时区"
      }[field] || field
    );
  }

  function formatState(stateName) {
    if (stateName === "tension") return "张力";
    if (stateName === "insufficient-data") return "资料不足";
    return stateName;
  }

  function inferFocusAreas(query) {
    const focus = [];
    const keywordMap = [
      ["感情", "relationship"],
      ["恋爱", "relationship"],
      ["婚姻", "relationship"],
      ["事业", "career"],
      ["工作", "career"],
      ["财运", "wealth"],
      ["健康", "health"],
      ["性格", "personality"]
    ];

    keywordMap.forEach(function (pair) {
      const keyword = pair[0];
      const dimension = pair[1];
      if (query.includes(keyword) && !focus.includes(dimension)) {
        focus.push(dimension);
      }
    });

    return focus.length ? focus : ["personality", "career", "relationship"];
  }

  function monthToSeason(dateValue) {
    if (!dateValue) return "未知季节";
    const month = new Date(dateValue).getMonth() + 1;
    if ([3, 4, 5].includes(month)) return "春季";
    if ([6, 7, 8].includes(month)) return "夏季";
    if ([9, 10, 11].includes(month)) return "秋季";
    return "冬季";
  }

  function timeBandLabel(timeValue) {
    if (!timeValue) return "未知时段";
    const hour = Number(timeValue.split(":")[0]);
    if (hour >= 5 && hour < 11) return "上午";
    if (hour >= 11 && hour < 14) return "中午";
    if (hour >= 14 && hour < 18) return "下午";
    if (hour >= 18 && hour < 22) return "傍晚";
    return "夜间";
  }

  function buildCustomCase(intake) {
    const query = (intake.query || "").trim();
    const name = (intake.name || "").trim();
    const birthDate = intake.birth_date || "";
    const birthTime = intake.birth_time || "";
    const birthPlace = (intake.birth_place || "").trim();
    const timezone = (intake.timezone || "").trim();

    if (!query) {
      throw new Error("先写一个你想分析的问题。");
    }

    const focusAreas = inferFocusAreas(query);
    const season = monthToSeason(birthDate);
    const timeBand = timeBandLabel(birthTime);
    const missing = [];

    if (!birthDate) missing.push("出生日期");
    if (!birthTime) missing.push("出生时辰");
    if (!birthPlace) missing.push("出生地点");
    if (!timezone) missing.push("时区");

    let completeness = "UNKNOWN";
    if (birthDate && birthTime && birthPlace && timezone) completeness = "EXACT";
    else if (birthDate) completeness = "DATE-ONLY";

    const issueStates = {
      career: focusAreas.includes("career") && completeness === "EXACT" ? "tension" : "insufficient-data",
      relationship: focusAreas.includes("relationship") && completeness === "EXACT" ? "tension" : "insufficient-data",
      personality:
        focusAreas.includes("personality") || focusAreas.includes("health")
          ? completeness === "UNKNOWN"
            ? "insufficient-data"
            : "tension"
          : "insufficient-data",
      risk: "insufficient-data"
    };

    const issues = Object.keys(issueStates).map(function (dimension, index) {
      const state = issueStates[dimension];
      return {
        dimension: dimensionLabel(dimension),
        state: state,
        rank: String(index + 1).padStart(2, "0"),
        desc:
          state === "tension"
            ? dimensionLabel(dimension) + "存在条件张力，需讲清边界。"
            : dimensionLabel(dimension) + "受资料完整度影响，暂不定论。"
      };
    });

    const openCount = issues.filter(function (item) {
      return item.state === "insufficient-data";
    }).length;
    const tensionCount = issues.filter(function (item) {
      return item.state === "tension";
    }).length;
    const subject = name || "你的输入";
    const missingText = missing.length ? "仍缺少" + missing.join("、") + "。" : "无关键缺口。";
    const focusText = focusAreas.map(dimensionLabel).join(" / ");
    const relationText =
      tensionCount > 0
        ? focusAreas.map(dimensionLabel).join("、") + "存在需保留边界的维度，其余部分按保守口径阅读。"
        : "以保守判断为主。";

    const reservations = [];
    if (missing.length) reservations.push("仍缺少" + missing.join("、") + "，结论按保守口径理解。");
    if (tensionCount > 0) reservations.push("存在条件性结论，需连同前提一起阅读。");
    if (openCount > 0) reservations.push("存在未裁决维度。");

    const followups = [];
    if (missing.length) followups.push("优先补" + missing.join("、") + "。");
    if (issueStates.career === "tension") followups.push("继续追问事业：哪些现实条件决定偏向？");
    if (issueStates.relationship === "tension") followups.push("继续追问感情：边界与稳定性落在什么阶段？");
    if (issueStates.personality === "tension") followups.push("继续追问性格：哪些行为特征会放大判断？");
    if (tensionCount > 0) followups.push("继续确认条件边界。");

    return {
      label: subject,
      note: "录入后即时生成。",
      summary:
        completeness === "EXACT"
          ? "问题“" + query + "”：以条件判断为主，高张力维度与未决项已拆开。"
          : "问题“" + query + "”：先按保守判断呈现。" + (missing.length ? "仍缺少" + missing.join("、") + "。" : ""),
      deliveryReadout:
        "前景：" +
        focusAreas.map(dimensionLabel).join("、") +
        "；条件：" +
        season +
        " / " +
        timeBand +
        " / 完整度。",
      completeness: completeness,
      missingText: missingText,
      focusText: focusText,
      relationText: relationText,
      claims: 4 + focusAreas.length,
      open: openCount,
      tension: tensionCount,
      trace: 5,
      chips: [
        { text: missing.length ? "资料有缺口" : "即时输入", color: missing.length ? "var(--accent-gold)" : "var(--accent-jade)" },
        { text: tensionCount ? "条件判断" : "保守判断", color: tensionCount ? "var(--accent)" : "var(--accent-gold)" }
      ],
      nodes: {
        career:
          issueStates.career === "tension"
            ? season + "与" + timeBand + "的节奏提示事业存在条件张力"
            : "事业更多受资料完整度影响",
        relationship:
          issueStates.relationship === "tension"
            ? "感情需要连同边界与互动节奏一起说明"
            : "感情暂按保守口径阅读",
        personality:
          issueStates.personality === "tension"
            ? "性格已进入可讨论区，但还不宜定论"
            : "性格暂不做单边裁决",
        risk: "风险主要来自资料缺口与解释敏感度"
      },
      issues: issues,
      sections: {
        consensus: ["这是录入后的即时推演结果。"],
        disagreement: issues
          .filter(function (item) {
            return item.state === "tension";
          })
          .map(function (item) {
            return item.dimension + "存在条件张力，不能压成一句总判词。";
          }),
        reservations: reservations,
        followups: followups
      }
    };
  }

  function normalizeWorkflowPayload(payload) {
    const request = payload.request || {};
    const report = payload.fusion_report || {};
    const issues = payload.debate_issues || [];
    const profile = payload.normalized_profile || {};
    const evidence = payload.system_evidence || [];
    const focusAreas = request.focus_areas || [];
    const openCount = issues.filter(function (item) {
      return item.status !== "closed";
    }).length;
    const tensionCount = issues.filter(function (item) {
      return item.relation === "tension" || item.relation === "contradiction";
    }).length;
    const claimCount = evidence.reduce(function (sum, item) {
      return sum + ((item.claims || []).length || 0);
    }, 0);
    const missing = profile.missing_fields || [];

    const issueMap = {};
    issues.forEach(function (item, index) {
      issueMap[item.dimension] = {
        dimension: dimensionLabel(item.dimension),
        state: item.relation === "tension" || item.relation === "contradiction" ? "tension" : "insufficient-data",
        rank: String(index + 1).padStart(2, "0"),
        desc: item.question
      };
    });

    return {
      label: "导入结果",
      note: "真实 workflow 渲染。",
      summary: report.summary || "缺少 summary。",
      deliveryReadout: "页面已切到真实结果视图。",
      completeness: String(profile.completeness || "UNKNOWN").toUpperCase(),
      missingText: missing.length ? "仍缺少" + missing.map(fieldLabel).join("、") + "。" : "无关键缺口。",
      focusText: focusAreas.length ? focusAreas.map(dimensionLabel).join(" / ") : "未显式标注",
      relationText: issues.length ? "共识、分歧与保留意见按 " + issues.length + " 个 issue 展开。" : "没有单独拉出 debate issue。",
      claims: claimCount,
      open: openCount,
      tension: tensionCount,
      trace: (payload.trace_metadata && payload.trace_metadata.steps && payload.trace_metadata.steps.length) || 0,
      chips: [
        { text: "真实结果", color: "var(--accent-jade)" },
        { text: openCount ? "保留未决项" : "已收束", color: openCount ? "var(--accent-gold)" : "var(--accent)" }
      ],
      nodes: {
        career: issueMap.career ? issueMap.career.desc : "事业未单独拉出高张力 issue。",
        relationship: issueMap.relationship ? issueMap.relationship.desc : "感情未单独拉出高张力 issue。",
        personality: issueMap.personality ? issueMap.personality.desc : "性格未单独拉出高张力 issue。",
        risk: issueMap.risk ? issueMap.risk.desc : "风险未单独拉出高张力 issue。"
      },
      issues: Object.keys(issueMap).length ? Object.keys(issueMap).map(function (key) { return issueMap[key]; }) : [
        { dimension: "无 issue", state: "insufficient-data", rank: "01", desc: "导入结果里没有 debate_issues。" }
      ],
      sections: {
        consensus: report.consensus_points || ["没有共识段落。"],
        disagreement: report.disagreement_points || ["没有分歧段落。"],
        reservations: report.reservations || ["没有保留意见。"],
        followups: report.suggested_followups || ["没有补充建议。"]
      }
    };
  }

  function createFallbackCase() {
    return CASE_DATA.full;
  }

  function initIntakePage() {
    const form = document.getElementById("intake-form");
    if (!form) return;

    const fields = {
      query: document.getElementById("field-query"),
      name: document.getElementById("field-name"),
      birth_date: document.getElementById("field-date"),
      birth_time: document.getElementById("field-time"),
      birth_place: document.getElementById("field-place"),
      timezone: document.getElementById("field-timezone")
    };
    const statusLine = document.getElementById("status-line");
    const loadDemo = document.getElementById("load-demo");
    const saved = safeRead(STORAGE_KEYS.intake);

    if (saved) {
      Object.keys(fields).forEach(function (key) {
        fields[key].value = saved[key] || "";
      });
    } else if (!fields.timezone.value) {
      fields.timezone.value = "Asia/Shanghai";
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (!fields.query.value.trim()) {
        statusLine.textContent = "请输入问题。";
        statusLine.classList.add("is-error");
        return;
      }

      statusLine.textContent = "正在进入…";
      statusLine.classList.remove("is-error");

      const payload = {};
      Object.keys(fields).forEach(function (key) {
        payload[key] = fields[key].value;
      });

      safeWrite(STORAGE_KEYS.intake, payload);
      window.sessionStorage.removeItem(STORAGE_KEYS.importedWorkflow);
      safeWrite(STORAGE_KEYS.selectedCase, "custom");
      window.location.href = "./analysis.html";
    });

    loadDemo.addEventListener("click", function () {
      safeWrite(STORAGE_KEYS.selectedCase, "full");
      window.location.href = "./analysis.html";
    });
  }

  function initAnalysisPage() {
    const viewport = document.querySelector("[data-page='analysis']");
    if (!viewport) return;

    const elements = {
      sourceLabel: document.getElementById("source-label"),
      sourceCopy: document.getElementById("source-copy"),
      caseTitle: document.getElementById("case-title"),
      caseSummary: document.getElementById("case-summary"),
      statusStrip: document.getElementById("status-strip"),
      metricClaims: document.getElementById("metric-claims"),
      metricOpen: document.getElementById("metric-open"),
      metricTension: document.getElementById("metric-tension"),
      metricTrace: document.getElementById("metric-trace"),
      deliveryReadout: document.getElementById("delivery-readout"),
      completenessText: document.getElementById("completeness-text"),
      completenessLabel: document.getElementById("completeness-label"),
      missingText: document.getElementById("missing-text"),
      focusText: document.getElementById("focus-text"),
      relationText: document.getElementById("relation-text"),
      nodeCareer: document.getElementById("node-career"),
      nodeRelationship: document.getElementById("node-relationship"),
      nodePersonality: document.getElementById("node-personality"),
      nodeRisk: document.getElementById("node-risk"),
      panelSummary: document.getElementById("panel-summary"),
      panelNote: document.getElementById("panel-note"),
      panelReadout: document.getElementById("panel-readout"),
      panelState: document.getElementById("panel-state"),
      issueList: document.getElementById("issue-list"),
      traceList: document.getElementById("trace-list"),
      listConsensus: document.getElementById("list-consensus"),
      listDisagreement: document.getElementById("list-disagreement"),
      listReservations: document.getElementById("list-reservations"),
      listFollowups: document.getElementById("list-followups"),
      customCaseButton: document.querySelector(".case-btn[data-case='custom']"),
      importDrawer: document.getElementById("import-drawer"),
      importJson: document.getElementById("import-json"),
      drawerStatus: document.getElementById("drawer-status")
    };

    const state = {
      activeCase: safeRead(STORAGE_KEYS.selectedCase) || "full"
    };

    function renderChips(chips) {
      elements.statusStrip.innerHTML = "";
      chips.forEach(function (chip) {
        const node = document.createElement("span");
        node.className = "chip";
        node.innerHTML = '<span class="chip-dot" style="--chip-color: ' + chip.color + ';"></span>' + chip.text;
        elements.statusStrip.appendChild(node);
      });
    }

    function renderList(target, items) {
      target.innerHTML = "";
      items.forEach(function (item) {
        const node = document.createElement("li");
        node.textContent = item;
        target.appendChild(node);
      });
    }

    function renderIssues(items) {
      elements.issueList.innerHTML = "";
      items.forEach(function (item) {
        const node = document.createElement("article");
        node.className = "issue-item";
        node.innerHTML =
          '<div class="issue-rank">' +
          item.rank +
          '</div>' +
          '<div class="issue-meta"><strong>' +
          item.dimension +
          '</strong><div class="issue-desc">' +
          item.desc +
          '</div></div>' +
          '<span class="issue-state" data-state="' +
          item.state +
          '">' +
          formatState(item.state) +
          "</span>";
        elements.issueList.appendChild(node);
      });
    }

    function renderTrace(stepCount, openCount) {
      const count = stepCount || TRACE_STEPS.length;
      elements.traceList.innerHTML = "";
      TRACE_STEPS.slice(0, count).forEach(function (step, index) {
        const node = document.createElement("article");
        node.className = "trace-item";
        node.innerHTML =
          "<strong>" +
          (index + 1) +
          ". " +
          step[0] +
          "</strong><span>" +
          step[1] +
          (index === count - 1 ? "，当前保留 " + openCount + " 个待补信息点。" : "。") +
          "</span>";
        elements.traceList.appendChild(node);
      });
    }

    function updateCaseButtons(activeCase) {
      document.querySelectorAll(".case-btn").forEach(function (button) {
        const isActive = button.dataset.case === activeCase;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
      });
    }

    function updateSourceMeta(source) {
      elements.sourceLabel.textContent = source.label;
      elements.sourceCopy.textContent = source.copy;
    }

    function resolveData(caseKey) {
      const imported = safeRead(STORAGE_KEYS.importedWorkflow);
      const intake = safeRead(STORAGE_KEYS.intake);

      if (imported && caseKey === "custom") {
        return {
          source: {
            label: "Workflow",
            copy: "真实结构结果"
          },
          data: normalizeWorkflowPayload(imported)
        };
      }

      if (caseKey === "custom" && intake) {
        return {
          source: {
            label: "Intake",
            copy: "来自录入"
          },
          data: buildCustomCase(intake)
        };
      }

      return {
        source: {
          label: "Demo",
          copy: "演示样例"
        },
        data: CASE_DATA[caseKey] || createFallbackCase()
      };
    }

    function render(caseKey) {
      const resolved = resolveData(caseKey);
      const data = resolved.data;
      state.activeCase = caseKey;
      safeWrite(STORAGE_KEYS.selectedCase, caseKey);

      updateSourceMeta(resolved.source);
      updateCaseButtons(caseKey);
      renderChips(data.chips || []);

      elements.caseTitle.textContent = data.label;
      elements.caseSummary.textContent = data.summary;
      elements.deliveryReadout.textContent = data.deliveryReadout;
      elements.completenessText.textContent = data.completeness;
      elements.completenessLabel.textContent = "资料完整度";
      elements.missingText.textContent = data.missingText;
      elements.focusText.textContent = data.focusText;
      elements.relationText.textContent = data.relationText;
      elements.nodeCareer.textContent = data.nodes.career;
      elements.nodeRelationship.textContent = data.nodes.relationship;
      elements.nodePersonality.textContent = data.nodes.personality;
      elements.nodeRisk.textContent = data.nodes.risk;
      elements.metricClaims.textContent = String(data.claims);
      elements.metricOpen.textContent = String(data.open);
      elements.metricTension.textContent = String(data.tension);
      elements.metricTrace.textContent = String(data.trace);
      elements.panelSummary.textContent = data.summary;
      elements.panelNote.textContent = data.note;
      elements.panelReadout.textContent = data.deliveryReadout;
      elements.panelState.textContent = data.missingText + " " + data.relationText;

      renderIssues(data.issues || []);
      renderTrace(data.trace, data.open);
      renderList(elements.listConsensus, data.sections.consensus || []);
      renderList(elements.listDisagreement, data.sections.disagreement || []);
      renderList(elements.listReservations, data.sections.reservations || []);
      renderList(elements.listFollowups, data.sections.followups || []);
    }

    function setActiveTab(tabName) {
      document.querySelectorAll(".tab-btn").forEach(function (button) {
        const isActive = button.dataset.tab === tabName;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
      });
      document.querySelectorAll(".tab-panel").forEach(function (panel) {
        panel.classList.toggle("is-active", panel.dataset.panel === tabName);
      });
    }

    function openDrawer() {
      elements.importDrawer.classList.add("is-open");
      elements.importDrawer.setAttribute("aria-hidden", "false");
    }

    function closeDrawer() {
      elements.importDrawer.classList.remove("is-open");
      elements.importDrawer.setAttribute("aria-hidden", "true");
    }

    if (safeRead(STORAGE_KEYS.intake)) {
      elements.customCaseButton.hidden = false;
    }

    document.querySelectorAll(".case-btn").forEach(function (button) {
      button.addEventListener("click", function () {
        render(button.dataset.case);
      });
    });

    document.querySelectorAll(".tab-btn").forEach(function (button) {
      button.addEventListener("click", function () {
        setActiveTab(button.dataset.tab);
      });
    });

    document.getElementById("back-to-intake").addEventListener("click", function () {
      window.location.href = "./index.html";
    });

    document.getElementById("open-import").addEventListener("click", openDrawer);
    document.getElementById("close-import").addEventListener("click", closeDrawer);

    elements.importDrawer.addEventListener("click", function (event) {
      if (event.target === elements.importDrawer) {
        closeDrawer();
      }
    });

    document.getElementById("load-demo-json").addEventListener("click", function () {
      elements.importJson.value = JSON.stringify(DEMO_WORKFLOW, null, 2);
      elements.drawerStatus.textContent = "已填入样例 JSON。";
    });

    document.getElementById("import-submit").addEventListener("click", function () {
      try {
        const payload = JSON.parse(elements.importJson.value);
        safeWrite(STORAGE_KEYS.importedWorkflow, payload);
        if (elements.customCaseButton.hidden) {
          elements.customCaseButton.hidden = false;
        }
        render("custom");
        closeDrawer();
      } catch (error) {
        elements.drawerStatus.textContent = "导入失败，请检查 JSON。";
      }
    });

    if (state.activeCase === "custom" && !safeRead(STORAGE_KEYS.intake) && !safeRead(STORAGE_KEYS.importedWorkflow)) {
      state.activeCase = "full";
    }

    setActiveTab("overview");
    render(state.activeCase);
  }

  initIntakePage();
  initAnalysisPage();
})();
