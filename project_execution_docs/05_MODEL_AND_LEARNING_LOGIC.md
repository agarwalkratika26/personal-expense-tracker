# 05 - Model & Learning Logic

This document details the classification mechanics, rule-based inference engine, and the design for how the system learns from user behavior and adapts its categorization over time.

---

## 1. Current Heuristic Inference Engine

Currently, the project uses a fast, zero-latency, offline rule-based heuristic model located in `src/expense_tracker/categorization.py`.

### 1.1 Mechanics
The engine maps merchant description tokens to canonical expense categories using keyword sets:

```python
CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "Groceries": ("grocery", "groceries", "supermarket", "market", "produce", "whole foods"),
    "Food & Dining": ("restaurant", "cafe", "coffee", "pizza", "takeaway", "dining", "food delivery"),
    "Transport": ("uber", "taxi", "transit", "bus", "train", "metro", "fuel", "gas station", "parking"),
    "Housing": ("rent", "mortgage", "landlord"),
    "Utilities": ("electric", "electricity", "water bill", "internet", "utility", "gas bill"),
    "Healthcare": ("pharmacy", "doctor", "hospital", "clinic", "medical", "dentist"),
    "Shopping": ("amazon", "bookstore", "clothing", "mall", "shopping", "store"),
    "Entertainment": ("movie", "cinema", "streaming", "spotify", "concert", "game"),
    "Education": ("course", "tuition", "school", "university", "udemy", "textbook"),
    "Travel": ("hotel", "flight", "airbnb", "airline", "vacation"),
    "Income": ("salary", "payroll", "paycheck", "freelance", "refund", "interest"),
}
```

### 1.2 Decision Tree & Execution Logic
1. **Income Check:** If `transaction_type == 'income'`, it is assigned `"Income"` directly.
2. **Text Normalization:**
   $$\text{text} = \text{regex\_replace}(\text{description.lower()}, \text{multiple\_spaces} \to \text{" "}).\text{strip}()$$
3. **Keyword Matching:**
   Iterates through each category's keyword tuple. If any keyword substring exists in `text`, that category is immediately returned.
4. **Fallback:**
   If no keywords match, it assigns `"Other"`.

---

## 2. Learning Mechanism: How the System Learns

In an expense tracking system, user feedback is the ground truth. As users manually correct categories, the system can learn and improve its predictions.

```
┌────────────────────────────────┐
│  Raw Transaction Description   │
└──────────────┬─────────────────┘
               │
               ▼
┌────────────────────────────────┐       No Match
│ Level 1: User Override Cache   │ ────────────────────┐
│ (Exact Match / High Precision) │                     │
└──────────────┬─────────────────┘                     │
               │ Match                                 │
               ▼                                       ▼
       [Return Category]             ┌────────────────────────────────┐
                                     │ Level 2: Rule-Based Heuristics │
                                     │ (Pre-defined Keyword Engine)   │
                                     └──────────────┬─────────────────┘
                                                    │ No Match
                                                    ▼
                                     ┌────────────────────────────────┐
                                     │ Level 3: Statistical / ML Model│
                                     │ (TF-IDF + Naive Bayes / LR)    │
                                     └──────────────┬─────────────────┘
                                                    │
                                                    ▼
                                            [Return Category]
```

### 2.1 Continuous Learning from User Corrections
1. **User Override Mapping (`user_rules` table):**
   When a user manually modifies the category of an imported transaction with description $D$ to category $C$, the system logs this pair:
   $$\text{UserCorrection}: D \to C$$
   Subsequent transactions matching $D$ immediately adopt $C$, overriding the default keywords.
2. **Dynamic Keyword Extraction:**
   When multiple descriptions containing token $w$ are consistently categorized as $C$, $w$ is dynamically promoted into the active keyword list for category $C$.

---

## 3. Future ML Classification Architecture

As transaction history grows ($N > 200$), the rule-based approach can be augmented with a lightweight machine learning pipeline:

### 3.1 Feature Extraction: TF-IDF
- **Tokenization:** Sub-word n-grams (character $3\text{-}5$ n-grams) and word-level tokens. This handles messy bank strings such as `"AMZN MKTP US*2A34"`.
- **Vectorization:** TF-IDF (Term Frequency - Inverse Document Frequency) maps variable-length merchant strings into dense feature vectors.

### 3.2 Classifier: Multinomial Naive Bayes / Logistic Regression
- **Training Set:** Historical labeled transactions from the user's database.
- **Confidence Scoring:** The model produces category probabilities:
  $$P(C_i \mid D) = \frac{P(D \mid C_i) P(C_i)}{P(D)}$$
- **Confidence Gate:**
  - If $\max_i P(C_i \mid D) \ge 0.75 \implies$ automatically assign category.
  - If $< 0.75 \implies$ flag as suggestion or fall back to `"Other"` for user confirmation.
