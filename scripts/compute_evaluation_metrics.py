"""
compute_evaluation_metrics.py — Statistical Evaluation Benchmark for CO2 and Scoring Engine

Computes:
1. System Scoring vs Human Ratings Correlation:
   - Spearman's Rank Correlation Coefficient (rho)
   - Pearson's Linear Correlation Coefficient (r)
   - Mean Absolute Error (MAE on 1-5 scale)
   - Root Mean Squared Error (RMSE on 1-5 scale)
   Across Overall, Semantic, Communication, and Structure dimensions.

2. VADER Sentiment Classifier Validation:
   - Evaluates VADER on a benchmark of 60 curated, balanced interview sentences
     (20 Positive, 20 Neutral, 20 Negative).
   - Computes Accuracy, Precision, Recall, Macro F1, and Weighted F1.
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.scoring import evaluate_answer
from modules.preprocessing import analyze_sentiment

# ---------------------------------------------------------------------------
# 1. 60 Curated Labeled Interview Sentences for VADER Evaluation
# ---------------------------------------------------------------------------
VADER_LABELED_SENTENCES = [
    # ── 20 Positive Interview Sentences ──
    {"text": "I am thrilled to have led our team to achieve a ninety-nine percent uptime.", "label": "Positive"},
    {"text": "Our cross-functional collaboration was an outstanding success and delivered early.", "label": "Positive"},
    {"text": "I really enjoy solving challenging algorithmic problems and optimizing performance.", "label": "Positive"},
    {"text": "The client loved our solution and immediately renewed their multi-year contract.", "label": "Positive"},
    {"text": "I took the initiative to mentor junior engineers, which significantly boosted morale.", "label": "Positive"},
    {"text": "My manager highlighted my contributions during the review and praised my velocity.", "label": "Positive"},
    {"text": "We successfully migrated the entire cluster with zero downtime and great results.", "label": "Positive"},
    {"text": "I am passionate about building scalable and maintainable distributed software systems.", "label": "Positive"},
    {"text": "This experience taught me effective leadership and strengthened our engineering culture.", "label": "Positive"},
    {"text": "Our automated testing suite caught critical regressions and improved code reliability.", "label": "Positive"},
    {"text": "I won first place at our company hackathon for an innovative AI search tool.", "label": "Positive"},
    {"text": "I am very proud of how our team rallied together during that demanding release cycle.", "label": "Positive"},
    {"text": "The feedback from users was overwhelmingly positive and engagement rose thirty percent.", "label": "Positive"},
    {"text": "I established a streamlined CI/CD pipeline that dramatically accelerated delivery.", "label": "Positive"},
    {"text": "It was a wonderful opportunity to learn modern cloud architecture best practices.", "label": "Positive"},
    {"text": "We cut infrastructure costs by forty percent through clever caching strategies.", "label": "Positive"},
    {"text": "My dedication to code quality resulted in zero critical bugs reported in production.", "label": "Positive"},
    {"text": "I communicated transparently with stakeholders and built strong trusted relationships.", "label": "Positive"},
    {"text": "The refactored module became twice as fast and much easier for colleagues to extend.", "label": "Positive"},
    {"text": "I am eager to contribute my expertise and grow alongside your exceptional team.", "label": "Positive"},

    # ── 20 Neutral Interview Sentences ──
    {"text": "Lists are mutable sequences in Python, while tuples are immutable fixed sequences.", "label": "Neutral"},
    {"text": "An INNER JOIN returns records that have matching keys in both participating tables.", "label": "Neutral"},
    {"text": "We scheduled bi-weekly sprint planning meetings on Tuesday mornings at ten o'clock.", "label": "Neutral"},
    {"text": "The system architecture consists of a React frontend and a FastAPI backend service.", "label": "Neutral"},
    {"text": "I used PostgreSQL as our primary relational database and Redis for caching sessions.", "label": "Neutral"},
    {"text": "Overfitting occurs when a statistical model memorizes training noise rather than patterns.", "label": "Neutral"},
    {"text": "My responsibilities included writing API endpoints and updating OpenAPI specifications.", "label": "Neutral"},
    {"text": "A LEFT JOIN preserves all rows from the left table and fills missing values with null.", "label": "Neutral"},
    {"text": "We deployed our microservices inside Docker containers managed by Kubernetes.", "label": "Neutral"},
    {"text": "The script reads input records from a CSV file and converts them to JSON format.", "label": "Neutral"},
    {"text": "Precision measures the proportion of positive predictions that were actually correct.", "label": "Neutral"},
    {"text": "Our backend communicates with third-party webhooks using standard HTTP POST requests.", "label": "Neutral"},
    {"text": "The function takes two integer arguments and returns a Boolean flag as output.", "label": "Neutral"},
    {"text": "I spent three years working as a software developer in the telecommunications industry.", "label": "Neutral"},
    {"text": "The pipeline runs automated unit tests on every pull request before merging to main.", "label": "Neutral"},
    {"text": "Decorators in Python wrap a target function to extend its behavior dynamically.", "label": "Neutral"},
    {"text": "The application handles incoming user authentication requests using JWT bearer tokens.", "label": "Neutral"},
    {"text": "We evaluated cross-entropy loss across ten distinct training epochs.", "label": "Neutral"},
    {"text": "The database schema has three foreign key constraints linking users to orders.", "label": "Neutral"},
    {"text": "I graduated with a bachelor of engineering degree in computer science last summer.", "label": "Neutral"},

    # ── 20 Negative / Challenging Interview Sentences ──
    {"text": "I made a critical error in deployment that caused an unexpected hour-long outage.", "label": "Negative"},
    {"text": "We missed the project deadline because several team members refused to cooperate.", "label": "Negative"},
    {"text": "Early in my career, severe public speaking anxiety made it hard to present my work.", "label": "Negative"},
    {"text": "I struggled with time management and felt overwhelmed by competing priorities.", "label": "Negative"},
    {"text": "There was a bitter conflict between two senior developers that stalled our progress.", "label": "Negative"},
    {"text": "Our initial prototype failed to meet performance benchmarks and crashed under load.", "label": "Negative"},
    {"text": "I was disappointed with my negative performance review regarding documentation gaps.", "label": "Negative"},
    {"text": "We lost an important client because of a bug that escaped into our production release.", "label": "Negative"},
    {"text": "I did not handle the client criticism well and initially responded too defensively.", "label": "Negative"},
    {"text": "The project was poorly planned, resulting in severe technical debt and team burnout.", "label": "Negative"},
    {"text": "I failed to write comprehensive integration tests, which led to painful regressions.", "label": "Negative"},
    {"text": "The legacy codebase was horribly convoluted and lacked any meaningful comments.", "label": "Negative"},
    {"text": "Our payment gateway integration suffered intermittent failures and transaction drops.", "label": "Negative"},
    {"text": "I panicked when the database server ran out of disk space during peak traffic.", "label": "Negative"},
    {"text": "Communication broke down between the frontend and backend teams during the sprint.", "label": "Negative"},
    {"text": "I made the mistake of pushing untested changes directly into the master branch.", "label": "Negative"},
    {"text": "We encountered constant friction when trying to agree on the database schema.", "label": "Negative"},
    {"text": "I had a hard time understanding asynchronous programming concepts in my first job.", "label": "Negative"},
    {"text": "The server response times degraded severely due to an unindexed query bottleneck.", "label": "Negative"},
    {"text": "It was stressful to debug memory leaks while customers complained about crashes.", "label": "Negative"},
]


def run_system_evaluation_metrics():
    """Evaluate system scores vs human ratings on synthetic_answers.csv."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic_answers.csv")
    df = pd.read_csv(csv_path)

    system_overall_100 = []
    system_overall_5 = []
    system_sem_100 = []
    system_comm_100 = []
    system_struct_100 = []

    human_overall = df["human_overall_rating"].tolist()
    human_sem = df["human_semantic_rating"].tolist()
    human_comm = df["human_communication_rating"].tolist()
    human_struct = df["human_structure_rating"].tolist()

    for _, row in df.iterrows():
        res = evaluate_answer(row["question_id"], row["candidate_answer"], candidate_level="final_year")
        ov = res["overall_score"]
        system_overall_100.append(ov)
        system_overall_5.append(ov / 20.0)
        system_sem_100.append(res["component_scores"]["semantic"] / 20.0)
        system_comm_100.append(res["component_scores"]["communication"] / 20.0)
        system_struct_100.append(res["component_scores"]["structure"] / 20.0)

    # Correlations & Errors for Overall Score
    spearman_rho, spearman_p = stats.spearmanr(system_overall_5, human_overall)
    pearson_r, pearson_p = stats.pearsonr(system_overall_5, human_overall)
    mae = float(np.mean(np.abs(np.array(system_overall_5) - np.array(human_overall))))
    rmse = float(np.sqrt(np.mean((np.array(system_overall_5) - np.array(human_overall)) ** 2)))

    # Component Correlations
    sem_rho, _ = stats.spearmanr(system_sem_100, human_sem)
    comm_rho, _ = stats.spearmanr(system_comm_100, human_comm)
    struct_rho, _ = stats.spearmanr(system_struct_100, human_struct)

    metrics = {
        "n_samples": len(df),
        "spearman_rho": round(spearman_rho, 4),
        "spearman_pvalue": spearman_p,
        "pearson_r": round(pearson_r, 4),
        "pearson_pvalue": pearson_p,
        "mae_5pt_scale": round(mae, 4),
        "rmse_5pt_scale": round(rmse, 4),
        "semantic_rho": round(sem_rho, 4),
        "communication_rho": round(comm_rho, 4),
        "structure_rho": round(struct_rho, 4),
    }
    return metrics


def run_vader_sentiment_metrics():
    """Evaluate VADER sentiment accuracy and F1 on 60 labeled interview sentences."""
    y_true = []
    y_pred = []

    for item in VADER_LABELED_SENTENCES:
        y_true.append(item["label"])
        res = analyze_sentiment(item["text"])
        y_pred.append(res["sentiment_label"])

    accuracy = accuracy_score(y_true, y_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro")
    prec_wt, rec_wt, f1_wt, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred, labels=["Positive", "Neutral", "Negative"])

    # Per-class metrics
    labels = ["Positive", "Neutral", "Negative"]
    p_class, r_class, f1_class, support = precision_recall_fscore_support(y_true, y_pred, labels=labels)

    class_report = {}
    for i, lbl in enumerate(labels):
        class_report[lbl] = {
            "precision": round(float(p_class[i]), 4),
            "recall": round(float(r_class[i]), 4),
            "f1_score": round(float(f1_class[i]), 4),
            "support": int(support[i]),
        }

    results = {
        "n_eval_sentences": len(VADER_LABELED_SENTENCES),
        "accuracy": round(float(accuracy), 4),
        "macro_precision": round(float(prec_macro), 4),
        "macro_recall": round(float(rec_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_wt), 4),
        "confusion_matrix": cm.tolist(),
        "per_class": class_report,
    }
    return results


if __name__ == "__main__":
    print("Computing System Evaluation Metrics on synthetic_answers.csv...")
    sys_metrics = run_system_evaluation_metrics()
    print(json.dumps(sys_metrics, indent=2))

    print("\nComputing VADER Sentiment Metrics on 60 Labeled Sentences...")
    vader_metrics = run_vader_sentiment_metrics()
    print(json.dumps(vader_metrics, indent=2))

    # Save to data/evaluation_metrics_benchmark.json for transparency
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "evaluation_metrics_benchmark.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"scoring_engine_benchmark": sys_metrics, "vader_sentiment_benchmark": vader_metrics}, f, indent=2)
    print(f"\nSaved metrics benchmark to {out_path}")
