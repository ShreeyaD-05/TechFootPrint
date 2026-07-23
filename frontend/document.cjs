const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, LevelFormat, ExternalHyperlink,
  ImageRun, TabStopType, TabStopPosition, SimpleField
} = require('docx');
const fs = require('fs');

// ─── Color Palette ───────────────────────────────────────────────────────────
const C = {
  darkBlue:   "1B3A6B",
  midBlue:    "2563EB",
  lightBlue:  "DBEAFE",
  accent:     "0EA5E9",
  green:      "16A34A",
  lightGreen: "DCFCE7",
  orange:     "EA580C",
  lightOrange:"FFF7ED",
  purple:     "7C3AED",
  lightPurp:  "EDE9FE",
  gray:       "374151",
  lightGray:  "F3F4F6",
  borderGray: "D1D5DB",
  white:      "FFFFFF",
  black:      "111827",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
const border = (c = C.borderGray) => ({ style: BorderStyle.SINGLE, size: 1, color: c });
const borders = (c = C.borderGray) => ({ top: border(c), bottom: border(c), left: border(c), right: border(c) });
const noBorder = () => ({ style: BorderStyle.NONE, size: 0, color: "FFFFFF" });
const noBorders = () => ({ top: noBorder(), bottom: noBorder(), left: noBorder(), right: noBorder() });

function txt(text, opts = {}) {
  return new TextRun({ text, font: "Arial", size: opts.size || 22, bold: opts.bold || false,
    color: opts.color || C.black, italics: opts.italic || false, ...opts });
}

function link(text, url) {
  return new ExternalHyperlink({
    link: url,
    children: [new TextRun({ text, font: "Arial", size: 20, color: C.midBlue,
      style: "Hyperlink", underline: { type: "single", color: C.midBlue } })]
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: C.darkBlue, space: 6 } },
    children: [new TextRun({ text, font: "Arial", size: 36, bold: true, color: C.darkBlue })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: C.midBlue })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: C.darkBlue })]
  });
}

function body(children, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 100, line: 320, lineRule: "auto" },
    alignment: opts.align || AlignmentType.LEFT,
    children
  });
}

function bullet(children, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { before: 40, after: 60 },
    children: typeof children === "string"
      ? [txt(children, { size: 22 })]
      : children
  });
}

function space(n = 1) {
  return Array(n).fill(new Paragraph({ spacing: { before: 0, after: 0 }, children: [txt("")] }));
}

function callout(label, text, bg = C.lightBlue, accent2 = C.midBlue) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [360, 8960],
    rows: [
      new TableRow({ children: [
        new TableCell({
          borders: noBorders(), width: { size: 360, type: WidthType.DXA },
          shading: { fill: accent2, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 80, right: 80 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: label, font: "Arial", size: 22, bold: true, color: C.white })] })]
        }),
        new TableCell({
          borders: noBorders(), width: { size: 8960, type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 160, right: 160 },
          children: [new Paragraph({ children: [txt(text, { size: 21 })] })]
        })
      ]})
    ]
  });
}

function infoBox(title, lines, bg = C.lightBlue, border2 = C.midBlue) {
  const rows = [
    new TableRow({ children: [
      new TableCell({
        borders: { top: border(border2), bottom: border(border2), left: { style: BorderStyle.SINGLE, size: 12, color: border2 }, right: border(border2) },
        width: { size: 9360, type: WidthType.DXA },
        shading: { fill: bg, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 60, left: 200, right: 200 },
        children: [new Paragraph({ children: [txt(title, { size: 22, bold: true, color: border2 })] })]
      })
    ]}),
    ...lines.map(line => new TableRow({ children: [
      new TableCell({
        borders: { top: noBorder(), bottom: noBorder(), left: { style: BorderStyle.SINGLE, size: 12, color: border2 }, right: noBorder() },
        width: { size: 9360, type: WidthType.DXA },
        shading: { fill: bg, type: ShadingType.CLEAR },
        margins: { top: 40, bottom: 40, left: 200, right: 200 },
        children: [new Paragraph({ children: typeof line === "string" ? [txt(line, { size: 20 })] : line })]
      })
    ]})),
  ];
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], rows });
}

function formulaBox(formula, label = "") {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [new TableCell({
      borders: { top: border(C.purple), bottom: border(C.purple), left: { style: BorderStyle.SINGLE, size: 16, color: C.purple }, right: border(C.purple) },
      width: { size: 9360, type: WidthType.DXA },
      shading: { fill: C.lightPurp, type: ShadingType.CLEAR },
      margins: { top: 120, bottom: 120, left: 240, right: 240 },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40, after: 40 },
          children: [new TextRun({ text: formula, font: "Courier New", size: 26, bold: true, color: C.purple })] }),
        ...(label ? [new Paragraph({ alignment: AlignmentType.CENTER,
          children: [txt(label, { size: 18, italic: true, color: C.gray })] })] : [])
      ]
    })]})],
  });
}

function headerRow(cells, widths, bg = C.darkBlue) {
  return new TableRow({
    tableHeader: true,
    children: cells.map((c, i) => new TableCell({
      borders: borders(C.borderGray),
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [txt(c, { bold: true, color: C.white, size: 20 })] })]
    }))
  });
}

function dataRow(cells, widths, shade = C.white) {
  return new TableRow({
    children: cells.map((c, i) => new TableCell({
      borders: borders(C.borderGray),
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: shade, type: ShadingType.CLEAR },
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
      children: [new Paragraph({ children: typeof c === "string" ? [txt(c, { size: 20 })] : c })]
    }))
  });
}

// ─── Document Build ───────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "\u25CB", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } } },
      ]},
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: C.darkBlue }, paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: C.midBlue }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: C.darkBlue }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [6000, 3360],
          rows: [new TableRow({ children: [
            new TableCell({
              borders: { top: noBorder(), bottom: border(C.midBlue), left: noBorder(), right: noBorder() },
              width: { size: 6000, type: WidthType.DXA },
              margins: { top: 0, bottom: 60, left: 0, right: 0 },
              children: [new Paragraph({ children: [
                new TextRun({ text: "Model-Free Derivative Pricing", font: "Arial", size: 18, bold: true, color: C.darkBlue })
              ]})]
            }),
            new TableCell({
              borders: { top: noBorder(), bottom: border(C.midBlue), left: noBorder(), right: noBorder() },
              width: { size: 3360, type: WidthType.DXA },
              margins: { top: 0, bottom: 60, left: 0, right: 0 },
              children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
                new TextRun({ text: "Vinay Kamble  |  Research Paper", font: "Arial", size: 18, italic: true, color: C.gray })
              ]})]
            })
          ]})]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.midBlue, space: 4 } },
          spacing: { before: 80 },
          tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
          children: [
            new TextRun({ text: "© 2025 Vinay Kamble — For Academic Use", font: "Arial", size: 16, color: C.gray }),
            new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: C.gray }),
            new SimpleField({ instruction: "PAGE", cachedValue: "1", dirty: false })
          ]
        })]
      })
    },
    children: [

      // ═══ COVER PAGE ═══════════════════════════════════════════════════════
      ...space(2),
      new Table({
        width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
        rows: [new TableRow({ children: [new TableCell({
          borders: noBorders(),
          shading: { fill: C.darkBlue, type: ShadingType.CLEAR },
          margins: { top: 400, bottom: 400, left: 400, right: 400 },
          children: [
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 80 }, children: [
              new TextRun({ text: "RESEARCH PAPER", font: "Arial", size: 20, bold: true, color: C.accent })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 }, children: [
              new TextRun({ text: "Model-Free Derivative Pricing", font: "Arial", size: 52, bold: true, color: C.white })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 80 }, children: [
              new TextRun({ text: "How to Price Options Without Assuming the Market Behaves Perfectly", font: "Arial", size: 24, italic: true, color: C.lightBlue })
            ]}),
            ...space(1),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              new TextRun({ text: "Vinay Kamble", font: "Arial", size: 28, bold: true, color: C.white })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 }, children: [
              new TextRun({ text: "Quantitative Finance & Machine Learning Researcher", font: "Arial", size: 20, italic: true, color: C.lightBlue })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              new TextRun({ text: "2025  |  For Engineers Entering Finance", font: "Arial", size: 20, color: C.lightBlue })
            ]}),
          ]
        })]})],
      }),
      ...space(2),

      callout("TLDR",
        "Derivatives (like stock options) need prices. Classical models assume markets follow neat math. Model-free pricing says: skip the math assumptions — just use what the market tells you. This paper explains how, using ML-friendly intuition.",
        C.lightBlue, C.midBlue),
      ...space(2),

      // ═══ SECTION 0: WHY YOU SHOULD CARE ══════════════════════════════════
      h1("0. Why This Matters — The Engineer's Perspective"),
      body([txt("You already understand models: you train them, test them, deploy them. But in finance, models do something unusual — they ", { size: 22 }),
        txt("set prices", { bold: true, size: 22 }), txt(" in markets worth trillions. When a model is wrong, entire banks collapse.", { size: 22 })]),

      ...space(1),
      infoBox("Real-World Stakes", [
        "2008 Financial Crisis — mis-pricing of mortgage derivatives caused a $22 trillion loss in US household wealth.",
        "LTCM Collapse (1998) — a hedge fund using classic models lost $4.6B when markets didn't follow the assumed distribution.",
        "Barings Bank (1995) — $1.3B lost, partly due to unhedged derivative positions.",
        "Source: Federal Reserve, BIS (Bank for International Settlements)"
      ], C.lightOrange, C.orange),
      ...space(1),

      body([txt("Model-free pricing is the engineering response: ", { size: 22 }), txt("don't assume. Measure.", { bold: true, size: 22 }),
        txt(" It extracts information directly from market data, just like you'd use data to train a model rather than hard-coding rules.", { size: 22 })]),
      ...space(2),

      // ═══ SECTION 1: WHAT IS A DERIVATIVE ═════════════════════════════════
      h1("1. What is a Derivative? (The 10-Minute Crash Course)"),
      body([txt("A ", { size: 22 }), txt("derivative", { bold: true, size: 22 }),
        txt(" is a financial contract whose value depends on something else (the 'underlying') — a stock, an index, oil, even the weather.", { size: 22 })]),
      ...space(1),

      h2("1.1  The Most Common Derivative: A Stock Option"),
      callout("CALL",
        "A CALL option gives the buyer the right (not obligation) to BUY a stock at price K (called the strike) before a date T. If the stock goes above K, you profit. Below K — you just lose what you paid (the premium).",
        C.lightGreen, C.green),
      ...space(1),
      callout("PUT",
        "A PUT option gives the right to SELL at price K. You profit if the stock falls below K. Think of it as an insurance policy on your stock portfolio.",
        C.lightOrange, C.orange),
      ...space(1),

      body([txt("Engineer analogy: A call option is like a ", { size: 22 }),
        txt("conditional function call", { bold: true, color: C.purple, size: 22 }),
        txt(" — payoff = max(S_T - K, 0) where S_T is stock price at expiry. You only 'execute' it if it's profitable.", { size: 22 })]),
      ...space(1),
      formulaBox("Payoff = max(S_T - K, 0)   [Call]     or     max(K - S_T, 0)   [Put]",
        "This is ALL you know for certain. The challenge is pricing this contract TODAY."),
      ...space(1),

      h2("1.2  Key Terms You'll Hear in the Lecture"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2500, 3700, 3160],
        rows: [
          headerRow(["Term", "Plain English", "ML Analogy"], [2500, 3700, 3160]),
          dataRow(["Strike Price (K)", "Price at which you exercise the option", "A threshold / decision boundary"], [2500, 3700, 3160], C.white),
          dataRow(["Expiry (T)", "When the contract ends", "Time horizon / forecast window"], [2500, 3700, 3160], C.lightGray),
          dataRow(["Premium", "Price paid today to own the option", "Cost of acquiring a feature"], [2500, 3700, 3160], C.white),
          dataRow(["Implied Volatility", "Market's forecast of future price swings", "Model uncertainty estimate"], [2500, 3700, 3160], C.lightGray),
          dataRow(["Risk-Neutral Measure", "Imaginary probability where all assets grow at risk-free rate", "A normalisation transform on probabilities"], [2500, 3700, 3160], C.white),
        ]
      }),
      ...space(2),

      // ═══ SECTION 2: CLASSICAL PRICING ════════════════════════════════════
      h1("2. Classical Pricing: Black-Scholes and Its Problems"),
      body([txt("Before model-free methods, the industry used the ", { size: 22 }),
        txt("Black-Scholes-Merton (BSM) model", { bold: true, size: 22 }),
        txt(" (1973), which won a Nobel Prize. It prices options with a closed-form formula.", { size: 22 })]),
      ...space(1),

      formulaBox("C = S0 * N(d1) - K * e^(-rT) * N(d2)",
        "BSM Call Price. N() = normal CDF, d1/d2 = functions of S, K, r, T, sigma"),
      ...space(1),

      h2("2.1  BSM Assumptions (Each is a Red Flag for Engineers)"),
      bullet([txt("Stock returns follow a ", { size: 22 }), txt("log-normal distribution", { bold: true, size: 22 }), txt(" (Gaussian, no fat tails)", { size: 22 })]),
      bullet([txt("Volatility (sigma) is ", { size: 22 }), txt("constant", { bold: true, size: 22 }), txt(" over the life of the option", { size: 22 })]),
      bullet([txt("Markets are ", { size: 22 }), txt("frictionless", { bold: true, size: 22 }), txt(" — no transaction costs, infinite liquidity", { size: 22 })]),
      bullet([txt("You can ", { size: 22 }), txt("trade continuously", { bold: true, size: 22 })]),
      ...space(1),

      infoBox("The Volatility Smile — Evidence BSM is Wrong", [
        "If BSM were correct, the implied volatility extracted from market prices would be FLAT across all strikes.",
        "In reality, it forms a 'smile' or 'skew' — options far from the current price have higher implied vol.",
        "This is the market pricing in crash risk and fat tails — things BSM ignores.",
        "Reference: Rubinstein (1994), 'Implied Binomial Trees', Journal of Finance"
      ], C.lightPurp, C.purple),
      ...space(1),

      body([txt("The volatility smile is ", { size: 22 }), txt("directly observable market data", { bold: true, size: 22 }),
        txt(". Model-free pricing exploits it rather than fighting it.", { size: 22 })]),
      ...space(2),

      // ═══ SECTION 3: MODEL-FREE — THE BIG IDEA ════════════════════════════
      h1("3. Model-Free Pricing — The Core Idea"),
      ...space(1),
      callout("KEY INSIGHT",
        "Instead of assuming how prices evolve, ask: what does the full set of market-traded option prices already tell us? Extract information directly from observed prices without specifying a model.",
        C.lightBlue, C.darkBlue),
      ...space(1),

      body([txt("In ML terms: model-free pricing is like ", { size: 22 }), txt("non-parametric inference", { bold: true, size: 22 }),
        txt(". You don't assume a functional form — you let the data speak. Contrast with BSM, which is like a ", { size: 22 }),
        txt("parametric model", { bold: true, size: 22 }), txt(" with Gaussian priors baked in.", { size: 22 })]),
      ...space(1),

      h2("3.1  The Two Foundations of Model-Free Pricing"),
      h3("Foundation 1: Breeden-Litzenberger (1978)"),
      body([txt("If you observe option prices C(K,T) for ALL strikes K at a fixed expiry T, you can recover the ", { size: 22 }),
        txt("risk-neutral probability density", { bold: true, size: 22 }), txt(" of the underlying at time T:", { size: 22 })]),
      formulaBox("q(K) = e^(rT) * d²C/dK²",
        "Second derivative of call price w.r.t. strike = risk-neutral density. No model assumed."),
      ...space(1),
      body([txt("Think of it as: you have a histogram of where the market thinks the stock will be at expiry. The ", { size: 22 }),
        txt("entire histogram", { bold: true, size: 22 }), txt(" is encoded in the option prices you observe in the market.", { size: 22 })]),
      ...space(1),

      h3("Foundation 2: Dupire's Local Volatility (1994)"),
      body([txt("Bruno Dupire showed you can extract a function sigma(S,t) — called ", { size: 22 }),
        txt("local volatility", { bold: true, size: 22 }),
        txt(" — from the market's implied vol surface. This produces a model that's ", { size: 22 }),
        txt("perfectly consistent", { bold: true, size: 22 }), txt(" with all observed option prices:", { size: 22 })]),
      formulaBox("sigma²(K,T) = 2 * [ dC/dT + r*K*dC/dK ] / [ K² * d²C/dK² ]",
        "Dupire's local vol formula — derived entirely from observable C(K,T) surface"),
      ...space(2),

      // ═══ SECTION 4: VIX — THE REAL WORLD EXAMPLE ═════════════════════════
      h1("4. The VIX — A Model-Free Index You've Heard Of"),
      body([txt("The VIX (CBOE Volatility Index) is ", { size: 22 }), txt("the most famous application of model-free pricing", { bold: true, size: 22 }),
        txt(". It measures the market's 30-day expected volatility of the S&P 500, computed entirely from option prices.", { size: 22 })]),
      ...space(1),

      h2("4.1  How VIX is Computed (Model-Free)"),
      formulaBox("VIX² ≈ (2/T) * Σ [ ΔKi / Ki² ] * exp(rT) * Q(Ki)",
        "Q(Ki) = market price of put or call at strike Ki. Sum over all listed strikes. No distributional assumption."),
      ...space(1),
      body([txt("Notice: ", { size: 22 }), txt("no model of stock price dynamics is assumed", { bold: true, size: 22 }),
        txt(". The formula is a weighted sum over ", { size: 22 }), txt("all available option contracts", { bold: true, size: 22 }),
        txt(", with the weights depending on the strike. This is model-free by design.", { size: 22 })]),
      ...space(1),

      infoBox("Live Reference: CBOE VIX Methodology", [
        [new TextRun({ text: "Official CBOE VIX White Paper (full derivation): ", font: "Arial", size: 20 }),
          link("https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf", "cboe.com/VIX_Methodology.pdf")],
        ["VIX is updated every 15 seconds from live S&P 500 option prices — fully automated model-free computation."],
        ["During the 2020 COVID crash, VIX hit 82.69 — the second highest ever. Model-based approaches couldn't anticipate this."],
      ], C.lightGreen, C.green),
      ...space(1),

      h2("4.2  Why VIX is So Useful"),
      bullet("It is a real-time measure of market fear — higher VIX = more uncertainty priced in"),
      bullet("It's used to price VIX futures and options, creating a whole derivative market on top of it"),
      bullet("Portfolio managers use VIX to hedge against market crashes"),
      bullet([txt("Academics use model-free volatility to ", { size: 22 }), txt("test whether models are correct", { bold: true, size: 22 }),
        txt(" — compare model-implied vol against VIX.", { size: 22 })]),
      ...space(2),

      // ═══ SECTION 5: STATIC REPLICATION ══════════════════════════════════
      h1("5. Static Replication — The Model-Free Pricing Engine"),
      body([txt("The most powerful technique in model-free pricing is ", { size: 22 }),
        txt("static replication", { bold: true, size: 22 }),
        txt(". The idea: you can replicate ANY payoff function f(S_T) by holding a portfolio of vanilla options (calls and puts) at various strikes.", { size: 22 })]),
      ...space(1),

      formulaBox("f(S_T) = f(κ) + f'(κ)(S_T - κ) + ∫[0 to κ] f''(K) P(K) dK + ∫[κ to ∞] f''(K) C(K) dK",
        "Carr-Madan decomposition: any payoff = a bond + forward + strip of puts + strip of calls"),
      ...space(1),

      body([txt("In plain English: ", { size: 22 }), txt("any complex payoff is just a weighted sum of puts and calls", { bold: true, size: 22 }),
        txt(". The weights are the second derivative of the payoff function. This is just numerical integration over observed market prices — no model needed.", { size: 22 })]),
      ...space(1),

      h2("5.1  Worked Example: Variance Swap"),
      body([txt("A variance swap pays the difference between ", { size: 22 }), txt("realised variance", { italic: true, size: 22 }),
        txt(" and ", { size: 22 }), txt("strike variance", { italic: true, size: 22 }),
        txt(". Its payoff is quadratic: f(S_T) = (log S_T)². Using Carr-Madan:", { size: 22 })]),
      formulaBox("E[Variance] = (2/T) * [ ∫[0 to F0] P(K)/K² dK + ∫[F0 to ∞] C(K)/K² dK ]",
        "Model-free variance = integral of option prices. F0 = today's forward price"),
      ...space(1),
      callout("INSIGHT",
        "The fair strike of a variance swap can be read directly from the options market — no model required. This is exactly what VIX computes! VIX² × T/2 ≈ fair variance.",
        C.lightPurp, C.purple),
      ...space(2),

      // ═══ SECTION 6: MODEL-FREE VS MODEL-BASED ═══════════════════════════
      h1("6. Model-Free vs Model-Based: A Direct Comparison"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2100, 3630, 3630],
        rows: [
          headerRow(["Property", "Model-Based (e.g. BSM)", "Model-Free"], [2100, 3630, 3630]),
          dataRow(["Inputs", "Model parameters (sigma, etc.)", "Observed option prices C(K,T)"], [2100, 3630, 3630], C.white),
          dataRow(["Assumptions", "Specific distribution of returns", "Arbitrage-free only"], [2100, 3630, 3630], C.lightGray),
          dataRow(["Accuracy", "Wrong when distribution is wrong", "Consistent with all market prices by construction"], [2100, 3630, 3630], C.white),
          dataRow(["Calibration", "Fit parameters to data", "Read prices directly from market"], [2100, 3630, 3630], C.lightGray),
          dataRow(["Risk Measures", "Model-dependent, can be misleading", "Model-free measures (VIX, skewness) more robust"], [2100, 3630, 3630], C.white),
          dataRow(["Extrapolation", "Can extrapolate to unobserved scenarios", "Limited to observed strikes range"], [2100, 3630, 3630], C.lightGray),
          dataRow(["ML Analogy", "Parametric model with Gaussian prior", "Non-parametric / kernel-based estimator"], [2100, 3630, 3630], C.white),
        ]
      }),
      ...space(2),

      // ═══ SECTION 7: MODEL-FREE RISK MEASURES ═════════════════════════════
      h1("7. Beyond Volatility: Model-Free Risk Measures"),
      body([txt("The same approach extends to higher moments and tail risks — all extracted from option prices without assuming a distribution.", { size: 22 })]),
      ...space(1),

      h2("7.1  Model-Free Skewness and Kurtosis"),
      body([txt("Bakshi, Kapadia & Madan (2003) showed you can extract the ", { size: 22 }), txt("risk-neutral skewness", { bold: true, size: 22 }),
        txt(" and ", { size: 22 }), txt("kurtosis", { bold: true, size: 22 }),
        txt(" of returns model-free from option prices. Skewness measures crash risk; kurtosis measures tail heaviness.", { size: 22 })]),
      formulaBox("SKEW = [ e^(rT)W3 - 3*mu*e^(rT)W2 + 2*mu³ ] / [ e^(rT)W2 - mu² ]^(3/2)",
        "W2, W3 = integrals of call and put prices with specific weights. mu = risk-neutral mean return."),
      ...space(1),

      h2("7.2  The CBOE SKEW Index"),
      body([txt("Just as VIX measures model-free volatility, the ", { size: 22 }), txt("CBOE SKEW Index", { bold: true, size: 22 }),
        txt(" measures model-free tail risk. A SKEW value of 100 means a symmetric distribution; higher values indicate greater left-tail risk (crash probability).", { size: 22 })]),
      ...space(1),

      infoBox("Live Reference: CBOE SKEW Index", [
        [new TextRun({ text: "CBOE SKEW Index overview: ", font: "Arial", size: 20 }),
          link("https://www.cboe.com/tradable_products/vix/vix_related_products/skew/", "cboe.com/skew")],
        ["SKEW rose above 150 before several market stress events — it's a leading indicator of tail risk."],
        ["Both VIX and SKEW are used together by risk managers at investment banks and hedge funds."],
      ], C.lightGreen, C.green),
      ...space(2),

      // ═══ SECTION 8: MACHINE LEARNING CONNECTIONS ════════════════════════
      h1("8. Machine Learning Meets Model-Free Pricing"),
      body([txt("Model-free pricing and modern ML are natural partners. Here are the most active research intersections:", { size: 22 })]),
      ...space(1),

      h2("8.1  Neural Networks as Option Pricing Functions"),
      body([txt("Instead of parametric formulas, train a ", { size: 22 }), txt("neural network", { bold: true, size: 22 }),
        txt(" on observed (strike, expiry, market data) → price. The network learns the pricing function directly from data.", { size: 22 })]),
      bullet([txt("Hutchinson, Lo & Poggio (1994) — first paper on neural net option pricing", { size: 22 })]),
      bullet([txt("Deep Hedging (Buehler et al., 2019, JPMorgan) — RL-based hedging without model assumption", { size: 22 })]),
      bullet([txt("Rough Volatility + Deep Learning — use fractional Brownian motion + nets for vol surfaces", { size: 22 })]),
      ...space(1),

      infoBox("Key Papers with Links", [
        [new TextRun({ text: "Deep Hedging (Buehler et al., 2019): ", font: "Arial", size: 20 }),
          link("https://arxiv.org/abs/1802.03042", "arxiv.org/abs/1802.03042")],
        [new TextRun({ text: "Neural Network Option Pricing (Hutchinson, 1994): ", font: "Arial", size: 20 }),
          link("https://www.nber.org/papers/w4718", "nber.org/papers/w4718")],
        [new TextRun({ text: "Volatility is Rough (Gatheral et al., 2018): ", font: "Arial", size: 20 }),
          link("https://arxiv.org/abs/1410.3394", "arxiv.org/abs/1410.3394")],
      ], C.lightPurp, C.purple),
      ...space(1),

      h2("8.2  Generative Models for Risk-Neutral Densities"),
      body([txt("Use a ", { size: 22 }), txt("Generative Adversarial Network (GAN)", { bold: true, size: 22 }),
        txt(" or ", { size: 22 }), txt("normalizing flow", { bold: true, size: 22 }),
        txt(" to learn the risk-neutral density directly. Constraints like no-arbitrage (density must be non-negative, integrate to 1) can be enforced as loss terms — exactly like constrained optimization in ML.", { size: 22 })]),
      ...space(1),

      h2("8.3  Interpolation and Surface Fitting"),
      body([txt("In practice, options are only listed at discrete strikes. Model-free pricing requires a ", { size: 22 }),
        txt("continuous surface", { bold: true, size: 22 }), txt(" C(K,T). This is a ", { size: 22 }),
        txt("regression problem", { bold: true, size: 22 }), txt(" — fit a smooth, arbitrage-free surface to sparse observations. Gaussian Processes, splines, and neural nets are all used.", { size: 22 })]),
      formulaBox("min_f  Σ [f(Ki,Ti) - Ci_market]²  +  λ * Reg(f)  s.t. Arbitrage Constraints",
        "Constrained regression: fit observed prices, regularize for smoothness, enforce no-arbitrage"),
      ...space(2),

      // ═══ SECTION 9: STEP BY STEP EXAMPLE ════════════════════════════════
      h1("9. Walk-Through: Computing Model-Free Variance Step by Step"),
      body([txt("Let's compute the fair variance (and hence VIX-like number) from a toy set of option prices. This is a computation any ML engineer can implement.", { size: 22 })]),
      ...space(1),

      h3("Step 1: Gather option prices at multiple strikes"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2340, 2340, 2340, 2340],
        rows: [
          headerRow(["Strike K", "Call Price C(K)", "Put Price P(K)", "Which to Use?"], [2340, 2340, 2340, 2340]),
          dataRow(["3800", "—", "42.5", "Put (K < F0)"], [2340, 2340, 2340, 2340], C.white),
          dataRow(["3900", "—", "21.3", "Put (K < F0)"], [2340, 2340, 2340, 2340], C.lightGray),
          dataRow(["4000 (F0)", "38.2", "38.2", "Average (ATM)"], [2340, 2340, 2340, 2340], C.white),
          dataRow(["4100", "19.8", "—", "Call (K > F0)"], [2340, 2340, 2340, 2340], C.lightGray),
          dataRow(["4200", "8.4", "—", "Call (K > F0)"], [2340, 2340, 2340, 2340], C.white),
        ]
      }),
      ...space(1),

      h3("Step 2: Apply the variance formula"),
      body([txt("For each strike, compute Q(Ki)/Ki² × ΔKi (where ΔKi = spacing between strikes = 100).", { size: 22 })]),
      body([txt("Sum: (42.5/3800² + 21.3/3900² + 38.2/4000² + 19.8/4100² + 8.4/4200²) × 100 × 2 × e^(rT)", { size: 22, italic: true })]),
      ...space(1),
      h3("Step 3: Annualise"),
      body([txt("Multiply by 2/T (where T = 30/365 for one month). Take the square root. Multiply by 100. You now have a VIX-like number.", { size: 22 })]),
      ...space(1),

      callout("CODE",
        "This is just a weighted sum — three lines in Python/NumPy. The 'model-free' nature means no simulation, no parameters — just arithmetic on market prices.",
        C.lightBlue, C.accent),
      ...space(1),

      infoBox("Python Reference Implementation", [
        [new TextRun({ text: "CBOE VIX Python implementation on GitHub: ", font: "Arial", size: 20 }),
          link("https://github.com/CBOE-Options-Institute/vix", "github.com/CBOE-Options-Institute/vix")],
        [new TextRun({ text: "QuantLib (C++/Python) for derivative pricing: ", font: "Arial", size: 20 }),
          link("https://www.quantlib.org/", "quantlib.org")],
        [new TextRun({ text: "py_vollib — practical option pricing library: ", font: "Arial", size: 20 }),
          link("https://github.com/vollib/py_vollib", "github.com/vollib/py_vollib")],
      ], C.lightGreen, C.green),
      ...space(2),

      // ═══ SECTION 10: LIMITATIONS ══════════════════════════════════════════
      h1("10. Limitations and Open Problems"),
      body([txt("Model-free pricing is not a free lunch. Key limitations:", { size: 22 })]),
      ...space(1),

      h2("10.1  Discrete Strike Problem"),
      body([txt("The Breeden-Litzenberger and Carr-Madan formulas require a ", { size: 22 }),
        txt("continuous", { bold: true, size: 22 }), txt(" range of strikes. Real markets have gaps. You must interpolate — and the interpolation method itself introduces assumptions.", { size: 22 })]),

      h2("10.2  Tail Extrapolation"),
      body([txt("Options are not listed at extreme strikes (S = 0 or S = infinity). You must assume some tail behavior — a hidden model. In practice, power-law or log-normal tails are assumed.", { size: 22 })]),

      h2("10.3  No Dynamics = Cannot Delta Hedge"),
      body([txt("Model-free pricing tells you the ", { size: 22 }), txt("price", { bold: true, size: 22 }), txt(" of a derivative. But to ", { size: 22 }),
        txt("hedge", { bold: true, size: 22 }), txt(" it (i.e., manage risk continuously), you need a model of price dynamics. This is where Deep Hedging (Section 8) fills the gap.", { size: 22 })]),

      h2("10.4  Market Microstructure"),
      body([txt("Bid-ask spreads, illiquidity, and option not trading simultaneously introduce noise into the observed C(K,T) surface. Robust filtering is needed — an active research area connecting directly to signal processing and ML.", { size: 22 })]),
      ...space(2),

      // ═══ SECTION 11: QUICK REFERENCE CHEAT SHEET ═════════════════════════
      h1("11. Quick Reference: Model-Free Pricing Cheat Sheet"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3000, 3500, 2860],
        rows: [
          headerRow(["Concept", "Formula / Method", "Use Case"], [3000, 3500, 2860]),
          dataRow(["Risk-Neutral Density", "q(K) = e^rT * d²C/dK²", "Full distribution of S_T"], [3000, 3500, 2860], C.white),
          dataRow(["Model-Free Variance", "2/T * ∫[P/K² + C/K²] dK", "VIX, variance swaps"], [3000, 3500, 2860], C.lightGray),
          dataRow(["Local Volatility", "Dupire formula", "Consistent vol surface"], [3000, 3500, 2860], C.white),
          dataRow(["Static Replication", "Carr-Madan decomposition", "Price exotic payoffs"], [3000, 3500, 2860], C.lightGray),
          dataRow(["Model-Free Skewness", "Bakshi-Kapadia-Madan", "Tail risk / crash risk"], [3000, 3500, 2860], C.white),
          dataRow(["Surface Interpolation", "Spline / GP / Neural Net", "Fill missing strikes"], [3000, 3500, 2860], C.lightGray),
        ]
      }),
      ...space(2),

      // ═══ SECTION 12: RESOURCES ════════════════════════════════════════════
      h1("12. Recommended Resources & Further Reading"),
      ...space(1),
      h2("Foundational Papers"),
      bullet([txt("Breeden & Litzenberger (1978) — 'Prices of State-Contingent Claims Implicit in Option Prices', ", { size: 21 }),
        link("https://www.jstor.org/stable/2352653", "jstor.org")]),
      bullet([txt("Dupire (1994) — 'Pricing with a Smile', Risk Magazine — ", { size: 21 }),
        link("https://www.risk.net/derivatives/1500690/pricing-with-a-smile", "risk.net")]),
      bullet([txt("Carr & Madan (1998) — 'Towards a Theory of Volatility Trading', ", { size: 21 }),
        link("https://engineering.nyu.edu/sites/default/files/2018-08/CarrMadan2.pdf", "engineering.nyu.edu")]),
      bullet([txt("Bakshi, Kapadia & Madan (2003) — 'Stock Return Characteristics, Skew Laws, and Differential Pricing of Individual Equity Options', Review of Financial Studies", { size: 21 })]),

      ...space(1),
      h2("Books"),
      bullet("'Volatility Surface' by Jim Gatheral — best practitioner book, freely available online"),
      bullet("'Dynamic Hedging' by Nassim Taleb — real-world option trading and model limits"),
      bullet("'Options, Futures and Other Derivatives' by John Hull — standard reference textbook"),

      ...space(1),
      h2("Online Courses & Tools"),
      bullet([txt("Coursera: 'Financial Engineering and Risk Management' (Columbia) — ", { size: 21 }),
        link("https://www.coursera.org/learn/financial-engineering-1", "coursera.org")]),
      bullet([txt("QuantLib documentation (Python bindings): ", { size: 21 }),
        link("https://quantlib-python-docs.readthedocs.io/", "quantlib-python-docs.readthedocs.io")]),
      bullet([txt("CBOE Education Center (free): ", { size: 21 }),
        link("https://www.cboe.com/education/", "cboe.com/education")]),
      bullet([txt("arXiv quantitative finance section: ", { size: 21 }),
        link("https://arxiv.org/list/q-fin.PR/recent", "arxiv.org/q-fin.PR")]),
      ...space(2),

      // ═══ CLOSING ══════════════════════════════════════════════════════════
      new Table({
        width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
        rows: [new TableRow({ children: [new TableCell({
          borders: { top: { style: BorderStyle.SINGLE, size: 6, color: C.darkBlue }, bottom: { style: BorderStyle.SINGLE, size: 6, color: C.darkBlue }, left: noBorder(), right: noBorder() },
          width: { size: 9360, type: WidthType.DXA },
          margins: { top: 200, bottom: 200, left: 0, right: 0 },
          children: [
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              new TextRun({ text: "Summary", font: "Arial", size: 28, bold: true, color: C.darkBlue })
            ]}),
            ...space(1),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              txt("Model-free pricing is the practice of extracting derivative prices and risk measures", { size: 22 })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              txt("directly from observed market data, without assuming a specific model for asset dynamics.", { size: 22 })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              txt("It is powerful because it is always consistent with what markets actually price,", { size: 22 })
            ]}),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              txt("and it connects deeply to non-parametric statistics and modern machine learning.", { size: 22 })
            ]}),
            ...space(1),
            new Paragraph({ alignment: AlignmentType.CENTER, children: [
              new TextRun({ text: "Vinay Kamble  —  2025", font: "Arial", size: 20, italic: true, color: C.gray })
            ]}),
          ]
        })]})],
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("./outputs/model_free_derivative_pricing.docx", buffer);
  console.log("Done.");
});