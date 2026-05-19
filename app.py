"""
Expense Tracker — app.py
Run:  pip install -r requirements.txt
      python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

from flask import Flask, render_template_string, request, redirect, url_for
import json, os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# ── Data persistence (JSON file) ────────────────────────────────────────────
DATA_FILE = "expenses.json"

def load_expenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_expenses(expenses):
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)

# ── Categories ───────────────────────────────────────────────────────────────
CATEGORIES = ["Food", "Transport", "Shopping", "Health", "Entertainment", "Bills", "Other"]

CATEGORY_ICONS = {
    "Food": "🍔", "Transport": "🚗", "Shopping": "🛍️",
    "Health": "💊", "Entertainment": "🎬", "Bills": "📄", "Other": "📦"
}

# ── HTML Template ─────────────────────────────────────────────────────────────
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Expense Tracker</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #f4f6fb;
      --card: #ffffff;
      --primary: #4f46e5;
      --primary-light: #eef2ff;
      --danger: #ef4444;
      --danger-light: #fef2f2;
      --text: #1e1b4b;
      --muted: #6b7280;
      --border: #e5e7eb;
      --radius: 12px;
      --shadow: 0 2px 16px rgba(79,70,229,0.08);
    }

    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 0 0 60px;
    }

    /* ── Header ── */
    header {
      background: var(--primary);
      color: white;
      padding: 22px 0 40px;
      text-align: center;
    }
    header h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
    header p  { font-size: 14px; opacity: 0.75; margin-top: 4px; }

    /* ── Container ── */
    .container { max-width: 760px; margin: -28px auto 0; padding: 0 16px; }

    /* ── Cards ── */
    .card {
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 24px;
      margin-bottom: 20px;
    }
    .card h2 {
      font-size: 15px;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 18px;
    }

    /* ── Summary row ── */
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-bottom: 20px;
    }
    .stat {
      background: var(--card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 18px 16px;
      text-align: center;
    }
    .stat .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; }
    .stat .value { font-size: 26px; font-weight: 700; color: var(--primary); margin-top: 6px; }
    .stat .value.red { color: var(--danger); }

    /* ── Form ── */
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group.full { grid-column: 1 / -1; }
    label { font-size: 13px; font-weight: 500; color: var(--muted); }

    input, select, textarea {
      padding: 10px 14px;
      border: 1.5px solid var(--border);
      border-radius: 8px;
      font-size: 15px;
      font-family: inherit;
      color: var(--text);
      background: var(--bg);
      transition: border-color 0.2s;
      outline: none;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--primary);
      background: #fff;
    }
    textarea { resize: vertical; min-height: 70px; }

    .btn {
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
      padding: 11px 22px;
      border-radius: 8px;
      border: none;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
    }
    .btn:active { transform: scale(0.97); }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { opacity: 0.9; }
    .btn-danger  { background: var(--danger-light); color: var(--danger); }
    .btn-danger:hover { background: #fde8e8; }
    .btn-sm { padding: 5px 12px; font-size: 13px; }

    .form-footer { margin-top: 18px; display: flex; justify-content: flex-end; }

    /* ── Flash messages ── */
    .flash { padding: 12px 18px; border-radius: 8px; margin-bottom: 16px;
             font-size: 14px; font-weight: 500; }
    .flash.success { background: #ecfdf5; color: #065f46; }
    .flash.error   { background: var(--danger-light); color: #991b1b; }

    /* ── Filter bar ── */
    .filter-bar {
      display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
      margin-bottom: 16px;
    }
    .filter-bar select, .filter-bar input {
      padding: 8px 12px; font-size: 13px; flex: 1; min-width: 120px;
    }
    .filter-bar .btn { padding: 8px 16px; font-size: 13px; }

    /* ── Expense list ── */
    .expense-item {
      display: flex; align-items: center; gap: 14px;
      padding: 14px 0;
      border-bottom: 1px solid var(--border);
    }
    .expense-item:last-child { border-bottom: none; }

    .cat-icon {
      width: 42px; height: 42px;
      border-radius: 10px;
      background: var(--primary-light);
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; flex-shrink: 0;
    }

    .expense-info { flex: 1; }
    .expense-title { font-weight: 600; font-size: 15px; }
    .expense-meta  { font-size: 12px; color: var(--muted); margin-top: 3px; }

    .expense-amount { font-size: 17px; font-weight: 700; color: var(--danger); margin-right: 12px; }

    /* ── Category breakdown ── */
    .cat-row {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 12px;
    }
    .cat-row:last-child { margin-bottom: 0; }
    .cat-label { width: 110px; font-size: 13px; color: var(--muted); flex-shrink: 0; }
    .bar-track { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
    .bar-fill  { height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.6s ease; }
    .cat-val   { font-size: 13px; font-weight: 600; color: var(--text); min-width: 60px; text-align: right; }

    /* ── Empty state ── */
    .empty { text-align: center; padding: 40px 20px; color: var(--muted); }
    .empty .icon { font-size: 48px; }
    .empty p     { margin-top: 10px; font-size: 15px; }

    @media (max-width: 500px) {
      .form-grid { grid-template-columns: 1fr; }
      .summary-grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>

<header>
  <h1>💸 Expense Tracker</h1>
  <p>Track your spending, stay in control</p>
</header>

<div class="container">

  {% for msg, cat in messages %}
  <div class="flash {{ cat }}">{{ msg }}</div>
  {% endfor %}

  <!-- Summary -->
  <div class="summary-grid">
    <div class="stat">
      <div class="label">Total Spent</div>
      <div class="value red">₹{{ "%.2f"|format(total) }}</div>
    </div>
    <div class="stat">
      <div class="label">This Month</div>
      <div class="value">₹{{ "%.2f"|format(this_month) }}</div>
    </div>
    <div class="stat">
      <div class="label">Entries</div>
      <div class="value">{{ expenses|length }}</div>
    </div>
  </div>

  <!-- Add Expense -->
  <div class="card">
    <h2>Add Expense</h2>
    <form method="POST" action="/add">
      <div class="form-grid">
        <div class="form-group">
          <label>Title</label>
          <input type="text" name="title" placeholder="e.g. Lunch at Cafe" required maxlength="80"/>
        </div>
        <div class="form-group">
          <label>Amount (₹)</label>
          <input type="number" name="amount" placeholder="0.00" step="0.01" min="0.01" required/>
        </div>
        <div class="form-group">
          <label>Category</label>
          <select name="category">
            {% for cat in categories %}
            <option value="{{ cat }}">{{ icons[cat] }} {{ cat }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="form-group">
          <label>Date</label>
          <input type="date" name="date" value="{{ today }}" required/>
        </div>
        <div class="form-group full">
          <label>Note (optional)</label>
          <textarea name="note" placeholder="Any additional details..."></textarea>
        </div>
      </div>
      <div class="form-footer">
        <button class="btn btn-primary" type="submit">＋ Add Expense</button>
      </div>
    </form>
  </div>

  <!-- Category Breakdown -->
  {% if expenses %}
  <div class="card">
    <h2>Breakdown by Category</h2>
    {% for cat, amt in cat_totals.items() %}
    <div class="cat-row">
      <div class="cat-label">{{ icons[cat] }} {{ cat }}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {{ (amt / total * 100)|round|int }}%"></div>
      </div>
      <div class="cat-val">₹{{ "%.0f"|format(amt) }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Expense List -->
  <div class="card">
    <h2>All Expenses</h2>

    <!-- Filter -->
    <form method="GET" action="/">
      <div class="filter-bar">
        <select name="filter_cat">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat }}" {% if filter_cat == cat %}selected{% endif %}>{{ cat }}</option>
          {% endfor %}
        </select>
        <input type="text" name="search" placeholder="Search..." value="{{ search }}"/>
        <button class="btn btn-primary" type="submit">Filter</button>
        <a href="/" class="btn" style="background:var(--border);color:var(--text);">Reset</a>
      </div>
    </form>

    {% if filtered_expenses %}
      {% for exp in filtered_expenses %}
      <div class="expense-item">
        <div class="cat-icon">{{ icons[exp.category] }}</div>
        <div class="expense-info">
          <div class="expense-title">{{ exp.title }}</div>
          <div class="expense-meta">
            {{ exp.category }} &nbsp;·&nbsp; {{ exp.date }}
            {% if exp.note %}&nbsp;·&nbsp; {{ exp.note }}{% endif %}
          </div>
        </div>
        <div class="expense-amount">₹{{ "%.2f"|format(exp.amount) }}</div>
        <form method="POST" action="/delete/{{ exp.id }}" onsubmit="return confirm('Delete this expense?')">
          <button class="btn btn-danger btn-sm" type="submit">✕</button>
        </form>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">
        <div class="icon">🧾</div>
        <p>No expenses found. Add your first one above!</p>
      </div>
    {% endif %}
  </div>

</div>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    expenses     = load_expenses()
    filter_cat   = request.args.get("filter_cat", "")
    search       = request.args.get("search", "").strip().lower()

    # Apply filters
    filtered = expenses
    if filter_cat:
        filtered = [e for e in filtered if e["category"] == filter_cat]
    if search:
        filtered = [e for e in filtered if search in e["title"].lower()
                    or search in e.get("note", "").lower()]

    # Stats
    total      = sum(e["amount"] for e in expenses)
    now        = datetime.now()
    this_month = sum(
        e["amount"] for e in expenses
        if e["date"].startswith(f"{now.year}-{now.month:02d}")
    )

    # Category totals (only from full expense list)
    cat_totals = defaultdict(float)
    for e in expenses:
        cat_totals[e["category"]] += e["amount"]
    cat_totals = dict(sorted(cat_totals.items(), key=lambda x: x[1], reverse=True))

    # Flash messages from query params
    messages = []
    if request.args.get("added"):
        messages.append(("Expense added successfully! ✓", "success"))
    if request.args.get("deleted"):
        messages.append(("Expense deleted.", "success"))

    return render_template_string(
        TEMPLATE,
        expenses=expenses,
        filtered_expenses=filtered,
        total=total,
        this_month=this_month,
        cat_totals=cat_totals,
        categories=CATEGORIES,
        icons=CATEGORY_ICONS,
        today=datetime.now().strftime("%Y-%m-%d"),
        filter_cat=filter_cat,
        search=search,
        messages=messages,
    )


@app.route("/add", methods=["POST"])
def add_expense():
    expenses = load_expenses()

    title    = request.form.get("title", "").strip()
    amount   = request.form.get("amount", "0")
    category = request.form.get("category", "Other")
    date     = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))
    note     = request.form.get("note", "").strip()

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return redirect(url_for("index"))

    new_expense = {
        "id":       len(expenses) + 1,
        "title":    title,
        "amount":   round(amount, 2),
        "category": category,
        "date":     date,
        "note":     note,
        "created":  datetime.now().isoformat(),
    }

    expenses.insert(0, new_expense)      # newest first
    save_expenses(expenses)

    return redirect(url_for("index", added=1))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expenses = load_expenses()
    expenses = [e for e in expenses if e["id"] != expense_id]
    save_expenses(expenses)
    return redirect(url_for("index", deleted=1))


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 50)
    print("  💸 Expense Tracker")
    print(f"  Local   → http://127.0.0.1:{port}")
    print(f"  Network → http://0.0.0.0:{port}  (all interfaces)")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=True)
